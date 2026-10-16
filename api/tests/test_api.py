from tests.conftest import PREFIX, enviar_venta, login_cliente, solicitar_otp


def test_flujo_completo(client, admin_headers):
    headers = login_cliente(client, "10101001", "3001112233", "Juan Perez")

    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert perfil.status_code == 200
    assert perfil.json()["cedula"] == "10101001"
    assert perfil.json()["telefono"] == "3001112233"

    venta = enviar_venta(client, "F-001", 20.0, 40000, telefono="3001112233", placa="abc123")
    assert venta.status_code == 200, venta.text
    assert venta.json()["puntos_otorgados"] == 20
    assert venta.json()["saldo"] == 20

    perfil2 = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert perfil2.json()["placa"] == "ABC123"

    duplicada = enviar_venta(client, "F-001", 20.0, 40000, telefono="3001112233")
    assert duplicada.status_code == 200
    assert duplicada.json()["duplicado"] is True
    assert duplicada.json()["saldo"] == 20

    recompensas = client.get(f"{PREFIX}/recompensas")
    assert recompensas.status_code == 200
    assert len(recompensas.json()) >= 1

    movimientos = client.get(f"{PREFIX}/clientes/me/movimientos", headers=headers)
    assert movimientos.status_code == 200
    assert len(movimientos.json()) == 1


def test_qr_y_venta_por_qr(client):
    headers = login_cliente(client, "10101002", "3009998877", "Maria")

    qr = client.get(f"{PREFIX}/clientes/me/qr", headers=headers)
    assert qr.status_code == 200
    payload = qr.json()["payload"]

    venta = enviar_venta(client, "F-QR-1", 30.0, 60000, qr_payload=payload)
    assert venta.status_code == 200, venta.text
    assert venta.json()["saldo"] == 30


def test_qr_invalido_rechazado(client):
    login_cliente(client, "10101003", "3005556677")
    resp = enviar_venta(client, "F-QR-BAD", 10.0, 20000, qr_payload="invalido.firma")
    assert resp.status_code == 400


def test_sync_requiere_api_key(client):
    login_cliente(client, "10101004", "3007778899")
    resp = client.post(
        f"{PREFIX}/sync/venta",
        json={"id_externo": "F-NOKEY", "volumen_litros": 5, "monto": 10000, "telefono": "3007778899"},
        headers={"X-API-Key": "clave-mala"},
    )
    assert resp.status_code == 401


def test_canje_y_reversion_admin(client, admin_headers):
    headers = login_cliente(client, "10101005", "3001234567", "Pedro")
    enviar_venta(client, "F-100", 300.0, 600000, telefono="3001234567")

    recompensas = client.get(f"{PREFIX}/recompensas").json()
    cafe = next(r for r in recompensas if r["nombre"] == "Cafe gratis")

    canje = client.post(f"{PREFIX}/canjes", json={"recompensa_id": cafe["id"]}, headers=headers)
    assert canje.status_code == 201, canje.text
    assert canje.json()["saldo"] == 200

    mis = client.get(f"{PREFIX}/canjes/mis", headers=headers)
    assert mis.status_code == 200
    assert len(mis.json()) == 1

    resumen = client.get(f"{PREFIX}/admin/resumen", headers=admin_headers)
    assert resumen.status_code == 200
    data = resumen.json()
    assert data["puntos_canjeados_mes"] == 100
    assert data["ventas_mes"]["cantidad"] >= 1


def test_admin_protegido(client):
    assert client.get(f"{PREFIX}/admin/resumen").status_code in (401, 403)
    assert client.get(f"{PREFIX}/admin/resumen", headers={"Authorization": "Bearer malo"}).status_code == 401


def test_otp_incorrecto(client):
    solicitar_otp(client, "10101006", "3000001111")
    resp = client.post(f"{PREFIX}/auth/otp/verify", json={"cedula": "10101006", "codigo": "000000"})
    assert resp.status_code == 400


def test_placa_del_cliente(client, admin_headers):
    login_cliente(client, "10101007", "3006665555", "Raul")
    venta = enviar_venta(client, "F-PL-1", 12.5, 25000, telefono="3006665555", placa="ab123cd")
    assert venta.status_code == 200, venta.text

    lista = client.get(f"{PREFIX}/admin/clientes?q=ab123cd", headers=admin_headers)
    assert lista.status_code == 200
    assert lista.json()["total"] == 1
    assert lista.json()["clientes"][0]["placa"] == "AB123CD"

    detalle = client.get(
        f"{PREFIX}/admin/clientes/{lista.json()['clientes'][0]['id']}", headers=admin_headers
    )
    assert detalle.status_code == 200
    assert detalle.json()["cliente"]["placa"] == "AB123CD"


def _crear_regla(client, admin_headers, nombre, **campos):
    body = {"nombre": nombre, "puntos_por_litro": 1.0, "prioridad": 0, "activa": True}
    body.update(campos)
    resp = client.post(f"{PREFIX}/admin/reglas", json=body, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _ver_regla(client, admin_headers, regla_id):
    resp = client.get(f"{PREFIX}/admin/reglas", headers=admin_headers)
    assert resp.status_code == 200
    return next(r for r in resp.json() if r["id"] == regla_id)


def test_editar_regla(client, admin_headers):
    regla_id = _crear_regla(client, admin_headers, "Promo")

    resp = client.put(
        f"{PREFIX}/admin/reglas/{regla_id}",
        json={
            "nombre": "Promo Invierno",
            "puntos_por_litro": 3.5,
            "prioridad": 5,
            "activa": False,
            "desde": "2026-01-01T00:00:00",
            "hasta": "2026-12-31T23:59:00",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["activa"] is False

    regla = _ver_regla(client, admin_headers, regla_id)
    assert regla["nombre"] == "Promo Invierno"
    assert regla["puntos_por_litro"] == 3.5
    assert regla["prioridad"] == 5
    assert regla["activa"] is False
    assert regla["desde"].startswith("2026-01-01")
    assert regla["hasta"].startswith("2026-12-31")


def test_editar_regla_parcial_preserva_fechas(client, admin_headers):
    desde = "2026-03-01T08:00:00"
    hasta = "2026-03-31T20:00:00"
    regla_id = _crear_regla(client, admin_headers, "Marzo", desde=desde, hasta=hasta)

    resp = client.put(f"{PREFIX}/admin/reglas/{regla_id}", json={"activa": False}, headers=admin_headers)
    assert resp.status_code == 200, resp.text

    regla = _ver_regla(client, admin_headers, regla_id)
    assert regla["activa"] is False
    assert regla["nombre"] == "Marzo"
    assert regla["puntos_por_litro"] == 1.0
    assert regla["desde"].startswith("2026-03-01")
    assert regla["hasta"].startswith("2026-03-31")

    resp = client.put(
        f"{PREFIX}/admin/reglas/{regla_id}", json={"puntos_por_litro": 4.0}, headers=admin_headers
    )
    assert resp.status_code == 200, resp.text

    regla = _ver_regla(client, admin_headers, regla_id)
    assert regla["puntos_por_litro"] == 4.0
    assert regla["nombre"] == "Marzo"
    assert regla["desde"].startswith("2026-03-01")
    assert regla["hasta"].startswith("2026-03-31")

    resp = client.put(
        f"{PREFIX}/admin/reglas/{regla_id}", json={"hasta": None, "desde": None}, headers=admin_headers
    )
    assert resp.status_code == 200, resp.text

    regla = _ver_regla(client, admin_headers, regla_id)
    assert regla["desde"] is None
    assert regla["hasta"] is None


def test_editar_regla_nombre_duplicado(client, admin_headers):
    _crear_regla(client, admin_headers, "Existente")
    otro = _crear_regla(client, admin_headers, "Otra")

    resp = client.put(
        f"{PREFIX}/admin/reglas/{otro}", json={"nombre": "Existente"}, headers=admin_headers
    )
    assert resp.status_code == 409

    resp = client.put(f"{PREFIX}/admin/reglas/{otro}", json={"nombre": "Otra"}, headers=admin_headers)
    assert resp.status_code == 200, resp.text


def test_editar_regla_rango_invalido(client, admin_headers):
    regla_id = _crear_regla(client, admin_headers, "Rango")

    resp = client.put(
        f"{PREFIX}/admin/reglas/{regla_id}",
        json={"desde": "2026-12-31T00:00:00", "hasta": "2026-01-01T00:00:00"},
        headers=admin_headers,
    )
    assert resp.status_code == 400

    resp = client.post(
        f"{PREFIX}/admin/reglas",
        json={
            "nombre": "Rango malo",
            "puntos_por_litro": 1.0,
            "prioridad": 0,
            "activa": True,
            "desde": "2026-12-31T00:00:00",
            "hasta": "2026-01-01T00:00:00",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_editar_regla_inexistente(client, admin_headers):
    resp = client.put(
        f"{PREFIX}/admin/reglas/99999", json={"nombre": "Nada"}, headers=admin_headers
    )
    assert resp.status_code == 404

