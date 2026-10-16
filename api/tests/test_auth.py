from tests.conftest import PREFIX, login_cliente, solicitar_otp


def test_identificar_inexistente(client):
    resp = client.post(f"{PREFIX}/auth/identificar", json={"cedula": "10909001"})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"existe": False, "telefono_parcial": None}


def test_auto_registro_y_login(client):
    ident = client.post(f"{PREFIX}/auth/identificar", json={"cedula": "10202001"})
    assert ident.json()["existe"] is False

    codigo = solicitar_otp(client, "10202001", "3112223344", "Maria Lopez")
    verify = client.post(f"{PREFIX}/auth/otp/verify", json={"cedula": "10202001", "codigo": codigo})
    assert verify.status_code == 200, verify.text
    assert verify.json()["cliente"]["cedula"] == "10202001"
    assert verify.json()["cliente"]["telefono"] == "3112223344"

    # segunda vez solo la cedula
    ident2 = client.post(f"{PREFIX}/auth/identificar", json={"cedula": "10202001"})
    assert ident2.json()["existe"] is True
    assert ident2.json()["telefono_parcial"] == "****3344"

    codigo2 = solicitar_otp(client, "10202001")
    verify2 = client.post(f"{PREFIX}/auth/otp/verify", json={"cedula": "10202001", "codigo": codigo2})
    assert verify2.status_code == 200


def test_cedula_nueva_requiere_telefono(client):
    resp = client.post(f"{PREFIX}/auth/otp/request", json={"cedula": "10707001"})
    assert resp.status_code == 400


def test_celular_duplicado(client):
    login_cliente(client, "10404001", "3008889999", "Ana")
    resp = client.post(f"{PREFIX}/auth/otp/request", json={"cedula": "10404002", "telefono": "3008889999"})
    assert resp.status_code == 409


def test_cedula_formato(client):
    body = {"cedula": "1.002.003"}
    codigo = solicitar_otp(client, "1.002.003", "3110001122", "Con Puntos")
    assert len(codigo) == 6
    ident = client.post(f"{PREFIX}/auth/identificar", json=body)
    assert ident.json()["existe"] is True
