from sqlalchemy import select

from app.models import AuditoriaCliente
from tests.conftest import PREFIX, crear_islero, enviar_venta, login_cliente


def _registro(placa: str, cedula: str, telefono: str, nombre: str | None = None) -> dict:
    body = {"placa": placa, "cedula": cedula, "telefono": telefono}
    if nombre:
        body["nombre"] = nombre
    return body


def test_login_islero_y_perfil(client, islero_headers):
    me = client.get(f"{PREFIX}/islero/me", headers=islero_headers)
    assert me.status_code == 200, me.text
    assert me.json()["usuario"] == "islero1"
    assert me.json()["nombre"] == "Islero Uno"


def test_islero_inactivo_no_entra(client, db):
    crear_islero(db, activo=False)
    resp = client.post(f"{PREFIX}/auth/islero", json={"usuario": "islero1", "password": "islero12345"})
    assert resp.status_code == 401, resp.text


def test_islero_no_accede_al_panel_admin(client, islero_headers):
    resp = client.get(f"{PREFIX}/admin/resumen", headers=islero_headers)
    assert resp.status_code == 403, resp.text


def test_registrar_cliente_nuevo(client, islero_headers, db):
    resp = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL101", "1000000001", "3000000001", "Cliente Uno"),
        headers=islero_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["creado"] is True
    assert data["actualizado"] is False
    assert data["placa"] == "ISL101"
    assert data["cedula"] == "1000000001"
    assert data["telefono"] == "3000000001"
    assert data["nombre"] == "Cliente Uno"
    assert data["placas"] == ["ISL101"]

    consulta = client.get(f"{PREFIX}/islero/clientes?placa=ISL101", headers=islero_headers)
    assert consulta.status_code == 200, consulta.text
    assert consulta.json()["existe"] is True
    assert consulta.json()["cliente"]["cedula"] == "1000000001"

    auditorias = db.scalars(select(AuditoriaCliente)).all()
    assert len(auditorias) == 1
    assert auditorias[0].accion == "crear"
    assert auditorias[0].placa == "ISL101"


def test_actualizar_datos_de_placa_existente(client, islero_headers, db):
    client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL102", "1000000002", "3000000002", "Nombre Viejo"),
        headers=islero_headers,
    )
    resp = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL102", "1000000003", "3000000003", "Nombre Nuevo"),
        headers=islero_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["creado"] is False
    assert data["actualizado"] is True
    assert data["cedula"] == "1000000003"
    assert data["telefono"] == "3000000003"
    assert data["nombre"] == "Nombre Nuevo"

    auditorias = db.scalars(select(AuditoriaCliente).order_by(AuditoriaCliente.id)).all()
    assert [a.accion for a in auditorias] == ["crear", "actualizar"]
    assert auditorias[1].detalle["antes"]["cedula"] == "1000000002"
    assert auditorias[1].detalle["despues"]["cedula"] == "1000000003"


def test_celular_existente_agrega_placa(client, islero_headers):
    primero = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL103", "1000000004", "3000000004", "Multivehiculo"),
        headers=islero_headers,
    )
    assert primero.status_code == 200, primero.text

    segundo = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL104", "1000000004", "3000000004"),
        headers=islero_headers,
    )
    assert segundo.status_code == 200, segundo.text
    assert segundo.json()["cliente_id"] == primero.json()["cliente_id"]
    assert set(segundo.json()["placas"]) == {"ISL103", "ISL104"}


def test_cedula_duplicada(client, islero_headers):
    client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL105", "1000000005", "3000000005"),
        headers=islero_headers,
    )
    resp = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL106", "1000000005", "3000000006"),
        headers=islero_headers,
    )
    assert resp.status_code == 409, resp.text
    assert "cedula" in resp.json()["detail"].lower()


def test_celular_duplicado_con_otra_cedula(client, islero_headers):
    client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL107", "1000000006", "3000000007"),
        headers=islero_headers,
    )
    resp = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL108", "1000000007", "3000000007"),
        headers=islero_headers,
    )
    assert resp.status_code == 409, resp.text
    assert "cedula" in resp.json()["detail"].lower()


def test_no_se_puede_pisar_la_cedula_de_otro_cliente(client, islero_headers):
    client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL109", "1000000008", "3000000008"),
        headers=islero_headers,
    )
    client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL110", "1000000009", "3000000009"),
        headers=islero_headers,
    )
    resp = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL109", "1000000009", "3000000008"),
        headers=islero_headers,
    )
    assert resp.status_code == 409, resp.text


def test_validaciones_de_formato(client, islero_headers):
    placa = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("AB12", "1000000010", "3000000010"),
        headers=islero_headers,
    )
    assert placa.status_code == 400, placa.text

    cedula = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL111", "123", "3000000010"),
        headers=islero_headers,
    )
    assert cedula.status_code == 400, cedula.text

    telefono = client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL111", "1000000010", "300000"),
        headers=islero_headers,
    )
    assert telefono.status_code == 400, telefono.text


def test_registro_permite_acumular_puntos_por_placa(client, islero_headers):
    client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL112", "1000000011", "3000000011", "Cliente Ventas"),
        headers=islero_headers,
    )
    venta = enviar_venta(client, "F-ISL-1", 20, 40000, placa="ISL112")
    assert venta.status_code == 200, venta.text
    assert venta.json()["puntos_otorgados"] == 20

    headers = login_cliente(client, "ISL112")
    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert perfil.status_code == 200, perfil.text
    assert perfil.json()["puntos"] == 20


def test_historial_de_registros_del_islero(client, islero_headers):
    client.post(
        f"{PREFIX}/islero/clientes",
        json=_registro("ISL113", "1000000012", "3000000012"),
        headers=islero_headers,
    )
    resp = client.get(f"{PREFIX}/islero/registros?limite=10", headers=islero_headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 1
    assert resp.json()[0]["placa"] == "ISL113"


def test_admin_crea_desactiva_y_resetea_islero(client, admin_headers):
    creado = client.post(
        f"{PREFIX}/admin/isleros",
        json={"usuario": "islero2", "nombre": "Islero Dos", "password": "claveSegura123"},
        headers=admin_headers,
    )
    assert creado.status_code == 201, creado.text
    islero_id = creado.json()["id"]

    login = client.post(f"{PREFIX}/auth/islero", json={"usuario": "islero2", "password": "claveSegura123"})
    assert login.status_code == 200, login.text
    assert login.json()["rol"] == "islero"

    lista = client.get(f"{PREFIX}/admin/isleros", headers=admin_headers)
    assert lista.status_code == 200, lista.text
    assert any(i["usuario"] == "islero2" for i in lista.json())

    desactivado = client.patch(
        f"{PREFIX}/admin/isleros/{islero_id}",
        json={"activo": False},
        headers=admin_headers,
    )
    assert desactivado.status_code == 200, desactivado.text
    assert client.post(
        f"{PREFIX}/auth/islero", json={"usuario": "islero2", "password": "claveSegura123"}
    ).status_code == 401

    reset = client.patch(
        f"{PREFIX}/admin/isleros/{islero_id}",
        json={"activo": True, "password": "otraClave123"},
        headers=admin_headers,
    )
    assert reset.status_code == 200, reset.text
    assert client.post(
        f"{PREFIX}/auth/islero", json={"usuario": "islero2", "password": "claveSegura123"}
    ).status_code == 401
    assert client.post(
        f"{PREFIX}/auth/islero", json={"usuario": "islero2", "password": "otraClave123"}
    ).status_code == 200


def test_admin_no_duplica_usuario_islero(client, admin_headers):
    body = {"usuario": "islero3", "nombre": "Islero Tres", "password": "claveSegura123"}
    assert client.post(f"{PREFIX}/admin/isleros", json=body, headers=admin_headers).status_code == 201
    assert client.post(f"{PREFIX}/admin/isleros", json=body, headers=admin_headers).status_code == 409
