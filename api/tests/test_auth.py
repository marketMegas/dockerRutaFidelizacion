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
    resp = client.post(f"{PREFIX}/auth/identificar", json={"placa": "ZZZ9001"})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"existe": False, "telefono_parcial": None}


def test_auto_registro_y_login(client):
    ident = client.post(f"{PREFIX}/auth/identificar", json={"placa": "TST2001"})
    assert ident.json()["existe"] is False

    codigo = solicitar_otp(client, "TST2001", "3112223344", "Maria Lopez")
    verify = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST2001", "codigo": codigo})
    assert verify.status_code == 200, verify.text
    assert verify.json()["cliente"]["placa"] == "TST2001"
    assert verify.json()["cliente"]["cedula"] is None
    assert verify.json()["cliente"]["telefono"] == "3112223344"

    # segunda vez solo la placa
    ident2 = client.post(f"{PREFIX}/auth/identificar", json={"placa": "TST2001"})
    assert ident2.json()["existe"] is True
    assert ident2.json()["telefono_parcial"] == "****3344"

    codigo2 = solicitar_otp(client, "TST2001")
    verify2 = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST2001", "codigo": codigo2})
    assert verify2.status_code == 200


def test_placa_nueva_requiere_telefono(client):
    resp = client.post(f"{PREFIX}/auth/otp/request", json={"placa": "TST7001"})
    assert resp.status_code == 400


def test_placa_invalida(client):
    resp = client.post(f"{PREFIX}/auth/otp/request", json={"placa": "AB12"})
    assert resp.status_code == 400
    assert "Placa" in resp.json()["detail"]


def test_celular_duplicado(client):
    login_cliente(client, "TST4001", "3008889999", "Ana")
    resp = client.post(f"{PREFIX}/auth/otp/request", json={"placa": "TST4002", "telefono": "3008889999"})
    assert resp.status_code == 409


def test_placa_formato(client):
    body = {"placa": "ab c-123"}
    codigo = solicitar_otp(client, "ab c-123", "3110001122", "Con Formato")
    assert len(codigo) == 6
    ident = client.post(f"{PREFIX}/auth/identificar", json=body)
    assert ident.json()["existe"] is True

    verify = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "ABC123", "codigo": codigo})
    assert verify.status_code == 200, verify.text
    assert verify.json()["cliente"]["placa"] == "ABC123"
