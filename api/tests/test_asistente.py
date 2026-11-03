import json

from sqlalchemy import select

from app.config import settings
from app.models import Cliente
from app.services import asistente, asistente_llm, rate_limit
from tests.conftest import PREFIX, enviar_venta, login_cliente


def _consulta(client, headers, mensaje, historial=None):
    body = {"mensaje": mensaje}
    if historial is not None:
        body["historial"] = historial
    return client.post(f"{PREFIX}/asistente/consulta", json=body, headers=headers)


def _cliente_actual(db):
    return db.scalar(select(Cliente).order_by(Cliente.id.desc()))


def test_asistente_requiere_sesion(client):
    resp = client.post(f"{PREFIX}/asistente/consulta", json={"mensaje": "¿Cuántos puntos tengo?"})
    assert resp.status_code == 401


def test_saldo_y_nivel(client):
    headers = login_cliente(client, "AST101", "3011110001", "Ana")
    enviar_venta(client, "AST-F-1", 300.0, 600000, telefono="3011110001")

    saldo = _consulta(client, headers, "¿Cuántos puntos tengo?")
    assert saldo.status_code == 200, saldo.text
    assert saldo.json()["intent"] == "saldo"
    assert saldo.json()["fuente"] == "reglas"
    assert "450" in saldo.json()["respuesta"]

    nivel = _consulta(client, headers, "¿Cuál es mi nivel y cuánto me falta para subir?")
    assert nivel.status_code == 200, nivel.text
    assert nivel.json()["intent"] == "nivel"
    assert "Oro" in nivel.json()["respuesta"]
    assert "Diamante" in nivel.json()["respuesta"]


def test_canjes_y_codigos_nunca_se_revelan(client):
    headers = login_cliente(client, "AST102", "3011110002", "Beto")
    enviar_venta(client, "AST-F-2", 300.0, 600000, telefono="3011110002")

    canje = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers)
    assert canje.status_code == 201, canje.text
    codigo = canje.json()["codigo"]

    lista = _consulta(client, headers, "¿Qué premios he canjeado?")
    assert lista.status_code == 200, lista.text
    assert lista.json()["intent"] == "lista_canjes"
    assert "Café gratis" in lista.json()["respuesta"]
    assert codigo not in json.dumps(lista.json(), ensure_ascii=False)

    donde = _consulta(client, headers, "¿Dónde veo mi código?")
    assert donde.status_code == 200, donde.text
    assert donde.json()["intent"] == "donde_codigo"
    assert "Recompensas" in donde.json()["respuesta"]
    assert codigo not in json.dumps(donde.json(), ensure_ascii=False)


def test_recompensas_y_falta_para_un_premio(client):
    headers = login_cliente(client, "AST103", "3011110003", "Carla")
    enviar_venta(client, "AST-F-3", 300.0, 600000, telefono="3011110003")
    client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers)

    premios = _consulta(client, headers, "¿Qué premios puedo canjear?")
    assert premios.status_code == 200, premios.text
    assert premios.json()["intent"] == "premios"
    assert any(p["nombre"] == "Lavada básica" for p in premios.json()["datos"]["premios"])

    lavada = _consulta(client, headers, "¿Cuánto me falta para la lavada?")
    assert lavada.status_code == 200, lavada.text
    assert lavada.json()["intent"] == "premio_especifico"
    assert "Lavada" in lavada.json()["respuesta"]
    assert "250" in lavada.json()["respuesta"]


def test_historial_de_movimientos(client):
    headers = login_cliente(client, "AST104", "3011110004", "Dora")
    enviar_venta(client, "AST-F-4", 20.0, 40000, telefono="3011110004")

    resp = _consulta(client, headers, "¿Cuáles son mis últimos movimientos?")
    assert resp.status_code == 200, resp.text
    assert resp.json()["intent"] == "movimientos"
    assert "Puntos ganados" in resp.json()["respuesta"]


def test_rate_limit(client, monkeypatch):
    headers = login_cliente(client, "AST105", "3011110005", "Eva")
    rate_limit._memoria.clear()
    monkeypatch.setattr(settings, "ASISTENTE_RATE_MAX", 1)

    primera = _consulta(client, headers, "Hola")
    segunda = _consulta(client, headers, "Hola de nuevo")
    assert primera.status_code == 200
    assert segunda.status_code == 429
    rate_limit._memoria.clear()


def test_llm_deshabilitado_usa_reglas(client):
    headers = login_cliente(client, "AST106", "3011110006", "Fabi")
    resp = _consulta(client, headers, "¿Qué es el programa de fidelización?")
    assert resp.status_code == 200, resp.text
    assert resp.json()["fuente"] == "reglas"
    assert resp.json()["intent"] == "desconocido"


def test_llm_opcional_responde(client, monkeypatch):
    headers = login_cliente(client, "AST107", "3011110007", "Gina")
    monkeypatch.setattr(settings, "ASISTENTE_LLM_ENABLED", True)
    monkeypatch.setattr("app.services.asistente.consultar_llm", lambda *args, **kwargs: "Respuesta del modelo")

    resp = _consulta(client, headers, "¿Qué es el programa de fidelización?")
    assert resp.status_code == 200, resp.text
    assert resp.json()["fuente"] == "llm"
    assert resp.json()["respuesta"] == "Respuesta del modelo"


def test_contexto_del_llm_sin_datos_personales_ni_codigos(client, db, monkeypatch):
    headers = login_cliente(client, "AST108", "3011110008", "Hugo", cedula="1098765432")
    enviar_venta(client, "AST-F-8", 300.0, 600000, telefono="3011110008", placa="AST108")
    canje = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers)
    assert canje.status_code == 201, canje.text
    codigo = canje.json()["codigo"]

    monkeypatch.setattr(settings, "ASISTENTE_LLM_ENABLED", True)
    monkeypatch.setattr(settings, "ASISTENTE_LLM_API_KEY", "clave-prueba")
    monkeypatch.setattr(settings, "ASISTENTE_LLM_MODEL", "modelo-prueba")

    capturado = {}

    class RespuestaFalsa:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "respuesta"}}]}

    class ClienteFalso:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json=None, headers=None):
            capturado["url"] = url
            capturado["payload"] = json
            return RespuestaFalsa()

    monkeypatch.setattr(asistente_llm.httpx, "Client", ClienteFalso)

    contexto = asistente.construir_contexto(db, _cliente_actual(db))
    assert asistente_llm.consultar_llm("¿Qué es el programa?", [], contexto) == "respuesta"

    enviado = json.dumps(capturado["payload"], ensure_ascii=False)
    assert codigo not in enviado
    assert "1098765432" not in enviado
    assert "3011110008" not in enviado
    assert "AST108" not in enviado
