from app.services import rate_limit
from tests.conftest import PREFIX, login_cliente, solicitar_otp


def test_rate_limit_fallback_usa_memoria():
    rate_limit._memoria.clear()
    rate_limit._cliente = None
    rate_limit._inicializado = True

    clave = "unit-test-rate-limit"
    assert rate_limit.permitir(clave, 2, 60)
    assert rate_limit.permitir(clave, 2, 60)
    assert not rate_limit.permitir(clave, 2, 60)


def test_identificar_inexistente(client):
    resp = client.post(f"{PREFIX}/auth/identificar", json={"placa": "ZZZ901"})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"existe": False, "telefono_parcial": None}


def test_auto_registro_y_login(client):
    ident = client.post(f"{PREFIX}/auth/identificar", json={"placa": "TST201"})
    assert ident.json()["existe"] is False

    codigo = solicitar_otp(client, "TST201", "3112223344", "Maria Lopez")
    verify = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST201", "codigo": codigo})
    assert verify.status_code == 200, verify.text
    assert verify.json()["cliente"]["placa"] == "TST201"
    assert verify.json()["cliente"]["cedula"] is None
    assert verify.json()["cliente"]["telefono"] == "3112223344"

    # segunda vez solo la placa
    ident2 = client.post(f"{PREFIX}/auth/identificar", json={"placa": "TST201"})
    assert ident2.json()["existe"] is True
    assert ident2.json()["telefono_parcial"] == "****3344"

    codigo2 = solicitar_otp(client, "TST201")
    verify2 = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST201", "codigo": codigo2})
    assert verify2.status_code == 200


def test_placa_nueva_requiere_telefono(client):
    resp = client.post(f"{PREFIX}/auth/otp/request", json={"placa": "TST701"})
    assert resp.status_code == 400


def test_placa_invalida(client):
    for placa in ("AB12", "ABC12", "ABC1234", "ABCD12", "A1C123", "ABC12D", "123ABC"):
        resp = client.post(f"{PREFIX}/auth/otp/request", json={"placa": placa})
        assert resp.status_code == 400, placa
        assert "Placa" in resp.json()["detail"]

    resp = client.post(f"{PREFIX}/auth/identificar", json={"placa": "ABC12"})
    assert resp.status_code == 400
    assert "Placa" in resp.json()["detail"]

    resp = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "ABC12", "codigo": "000000"})
    assert resp.status_code == 400
    assert "Placa" in resp.json()["detail"]


def test_celular_existente_agrega_placa(client):
    login_cliente(client, "TST401", "3008889999", "Ana")
    codigo = solicitar_otp(client, "TST402", "3008889999")
    verify = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST402", "codigo": codigo})
    assert verify.status_code == 200, verify.text
    assert set(verify.json()["cliente"]["placas"]) == {"TST401", "TST402"}

    # es la misma cuenta: entra con la segunda placa y ve ambos vehiculos
    codigo2 = solicitar_otp(client, "TST401")
    verify2 = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST401", "codigo": codigo2})
    assert verify2.json()["cliente"]["telefono"] == "3008889999"
    assert len(verify2.json()["cliente"]["placas"]) == 2


def test_misma_cuenta_comparte_saldo(client):
    headers = login_cliente(client, "TST404", "3002224455", "Sara")
    codigo = solicitar_otp(client, "TST405", "3002224455")
    client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST405", "codigo": codigo})

    venta = client.post(
        f"{PREFIX}/sync/venta",
        json={
            "id_externo": "F-MULTI-1",
            "volumen_litros": 30,
            "monto": 60000,
            "telefono": "3002224455",
            "placa": "TST404",
        },
        headers={"X-API-Key": "test-key"},
    )
    assert venta.status_code == 200, venta.text
    assert venta.json()["saldo"] == 30

    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert perfil.json()["puntos"] == 30
    assert set(perfil.json()["placas"]) == {"TST404", "TST405"}


def test_placa_formato(client):
    body = {"placa": "ab c-123"}
    codigo = solicitar_otp(client, "ab c-123", "3110001122", "Con Formato")
    assert len(codigo) == 6

    verify = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "ABC123", "codigo": codigo})
    assert verify.status_code == 200, verify.text
    assert verify.json()["cliente"]["placa"] == "ABC123"

    ident = client.post(f"{PREFIX}/auth/identificar", json=body)
    assert ident.json()["existe"] is True
