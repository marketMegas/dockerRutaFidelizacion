import json

import pytest

from app.services import catalogo
from tests.conftest import CATALOGO_TEST, PREFIX


def _catalogo_valido() -> dict:
    return {
        "version": 1,
        "niveles": [
            {"clave": "arranque", "nombre": "Arranque", "minimo": 0, "multiplicador": 1.0},
            {"clave": "plata", "nombre": "Plata", "minimo": 100, "multiplicador": 1.25},
        ],
        "premios": [
            {
                "clave": "cafe",
                "nombre": "Cafe gratis",
                "descripcion": "Un cafe",
                "imagen": "",
                "costo_puntos": 100,
                "activo": True,
                "codigos": ["AAAA-2345", "BBBB-6789"],
            }
        ],
    }


def test_el_archivo_se_crea_desde_la_plantilla():
    assert CATALOGO_TEST.exists()
    datos = catalogo.leer()
    assert len(datos["niveles"]) == 4
    assert [n["clave"] for n in datos["niveles"]] == ["arranque", "plata", "oro", "diamante"]
    assert [n["minimo"] for n in datos["niveles"]] == [1, 100, 250, 500]
    assert datos["premios"][0]["clave"] == "cafe"
    assert len(datos["premios"][0]["codigos"]) == 100


def test_normalizar_codigo():
    assert catalogo.normalizar_codigo("abcd-2345") == "ABCD-2345"
    assert catalogo.normalizar_codigo("ABCD2345") == "ABCD-2345"
    assert catalogo.normalizar_codigo(" abcd2345 ") == "ABCD-2345"
    assert catalogo.normalizar_codigo("AB0D-2345") == "AB0D-2345"
    assert catalogo.normalizar_codigo("AB1D-2345") == "AB1D-2345"
    assert catalogo.normalizar_codigo("OIL0-1L2O") == "OIL0-1L2O"
    assert catalogo.normalizar_codigo("ABC") is None
    assert catalogo.normalizar_codigo("AB-D2345") is None
    assert catalogo.normalizar_codigo(None) is None


def test_guardar_incrementa_la_version():
    datos = _catalogo_valido()
    guardado = catalogo.guardar(datos, version_esperada=1)
    assert guardado["version"] == 2
    assert catalogo.leer()["version"] == 2


def test_guardar_con_version_desactualizada_da_conflicto():
    with pytest.raises(catalogo.ConflictoCatalogo):
        catalogo.guardar(_catalogo_valido(), version_esperada=99)


def test_codigo_invalido_es_rechazado():
    datos = _catalogo_valido()
    datos["premios"][0]["codigos"] = ["corto"]
    with pytest.raises(catalogo.CatalogoInvalido):
        catalogo.validar(datos)


def test_codigo_repetido_es_rechazado():
    datos = _catalogo_valido()
    datos["premios"][0]["codigos"] = ["AAAA-2345", "AAAA-2345"]
    with pytest.raises(catalogo.CatalogoInvalido):
        catalogo.validar(datos)


def test_nivel_con_multiplicador_invalido_es_rechazado():
    datos = _catalogo_valido()
    datos["niveles"][1]["multiplicador"] = 0
    with pytest.raises(catalogo.CatalogoInvalido):
        catalogo.validar(datos)


def test_el_archivo_guardado_es_json_valido():
    catalogo.guardar(_catalogo_valido(), version_esperada=1)
    with CATALOGO_TEST.open(encoding="utf-8") as archivo:
        datos = json.load(archivo)
    assert datos["version"] == 2
    assert datos["premios"][0]["codigos"] == ["AAAA-2345", "BBBB-6789"]


def test_admin_actualiza_el_catalogo(client, admin_headers):
    actual = client.get(f"{PREFIX}/admin/catalogo", headers=admin_headers)
    assert actual.status_code == 200
    assert actual.json()["version"] == 1
    assert len(actual.json()["niveles"]) == 4

    cuerpo = {
        "version": actual.json()["version"],
        "niveles": actual.json()["niveles"],
        "premios": actual.json()["premios"],
    }
    cuerpo["niveles"][1]["minimo"] = 120

    resp = client.put(f"{PREFIX}/admin/catalogo", json=cuerpo, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["version"] == 2

    nuevo = client.get(f"{PREFIX}/admin/catalogo", headers=admin_headers).json()
    assert nuevo["niveles"][1]["minimo"] == 120


def test_admin_choca_con_una_version_desactualizada(client, admin_headers):
    cuerpo = {
        "version": 99,
        "niveles": [{"clave": "arranque", "nombre": "Arranque", "minimo": 0, "multiplicador": 1.0}],
        "premios": [],
    }
    resp = client.put(f"{PREFIX}/admin/catalogo", json=cuerpo, headers=admin_headers)
    assert resp.status_code == 409


def test_el_catalogo_publico_no_expone_los_codigos(client):
    resp = client.get(f"{PREFIX}/catalogo")
    assert resp.status_code == 200
    premio = resp.json()["premios"][0]
    assert "codigos" not in premio
    assert premio["codigos_disponibles"] == 100


def test_el_endpoint_de_generar_codigos_no_existe(client, admin_headers):
    resp = client.post(
        f"{PREFIX}/admin/catalogo/cafe/codigos",
        json={"cantidad": 1},
        headers=admin_headers,
    )
    assert resp.status_code == 404
