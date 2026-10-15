from tests.conftest import PREFIX, enviar_venta, login_cliente, solicitar_otp


def test_flujo_completo(client, admin_headers):
    headers = login_cliente(client, "3001112233", "Juan Perez")

    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert perfil.status_code == 200
    assert perfil.json()["telefono"] == "3001112233"

    venta = enviar_venta(client, "F-001", 20.0, 40000, telefono="3001112233")
    assert venta.status_code == 200, venta.text
    assert venta.json()["puntos_otorgados"] == 20
    assert venta.json()["saldo"] == 20

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
    headers = login_cliente(client, "3009998877", "Maria")

    qr = client.get(f"{PREFIX}/clientes/me/qr", headers=headers)
    assert qr.status_code == 200
    payload = qr.json()["payload"]

    venta = enviar_venta(client, "F-QR-1", 30.0, 60000, qr_payload=payload)
    assert venta.status_code == 200, venta.text
    assert venta.json()["saldo"] == 30


def test_qr_invalido_rechazado(client):
    login_cliente(client, "3005556677")
    resp = enviar_venta(client, "F-QR-BAD", 10.0, 20000, qr_payload="invalido.firma")
    assert resp.status_code == 400


def test_sync_requiere_api_key(client):
    login_cliente(client, "3007778899")
    resp = client.post(
        f"{PREFIX}/sync/venta",
        json={"id_externo": "F-NOKEY", "volumen_litros": 5, "monto": 10000, "telefono": "3007778899"},
        headers={"X-API-Key": "clave-mala"},
    )
    assert resp.status_code == 401


def test_canje_y_reversion_admin(client, admin_headers):
    headers = login_cliente(client, "3001234567", "Pedro")
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
    solicitar_otp(client, "3000001111")
    resp = client.post(f"{PREFIX}/auth/otp/verify", json={"telefono": "3000001111", "codigo": "000000"})
    assert resp.status_code == 400
