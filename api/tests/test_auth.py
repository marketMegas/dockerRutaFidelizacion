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


def test_admin_login_rate_limit(client, monkeypatch):
    from app.config import settings

    rate_limit._memoria.clear()
    rate_limit._cliente = None
    rate_limit._inicializado = True
    monkeypatch.setattr(settings, "ADMIN_RATE_MAX", 2)

    malas = {"usuario": "admin", "password": "incorrecta"}
    assert client.post(f"{PREFIX}/auth/admin", json=malas).status_code == 401
    assert client.post(f"{PREFIX}/auth/admin", json=malas).status_code == 401
    bloqueado = client.post(f"{PREFIX}/auth/admin", json=malas)
    assert bloqueado.status_code == 429, bloqueado.text

    buenas = {"usuario": "admin", "password": "admin123"}
    assert client.post(f"{PREFIX}/auth/admin", json=buenas).status_code == 429


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
    assert verify.json()["cliente"]["cedula"] == "3112223344"
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


def test_registro_requiere_cedula(client):
    resp = client.post(f"{PREFIX}/auth/otp/request", json={"placa": "TST301", "telefono": "3115556677"})
    assert resp.status_code == 400, resp.text
    assert "cedula" in resp.json()["detail"].lower()


def test_cedula_invalida(client):
    for cedula in ("12345", "abcdef", "12345678901"):
        resp = client.post(
            f"{PREFIX}/auth/otp/request",
            json={"placa": "TST302", "telefono": "3115556688", "cedula": cedula},
        )
        assert resp.status_code == 400, cedula
        assert "cedula" in resp.json()["detail"].lower()


def test_cedula_duplicada(client):
    login_cliente(client, "TST303", "3115556699", "Uno")
    resp = client.post(
        f"{PREFIX}/auth/otp/request",
        json={"placa": "TST304", "telefono": "3115556700", "cedula": "3115556699"},
    )
    assert resp.status_code == 409, resp.text
    assert "cedula" in resp.json()["detail"].lower()


def test_placa_nueva_con_cedula_distinta(client):
    login_cliente(client, "TST305", "3115556711", "Cuenta")
    resp = client.post(
        f"{PREFIX}/auth/otp/request",
        json={"placa": "TST306", "telefono": "3115556711", "cedula": "9999999999"},
    )
    assert resp.status_code == 409, resp.text


def test_actualizar_cedula_perfil(client):
    headers = login_cliente(client, "TST307", "3115556722", "Perfil")
    resp = client.patch(f"{PREFIX}/clientes/me", json={"cedula": "1098765432"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["cedula"] == "1098765432"

    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers).json()
    assert perfil["cedula"] == "1098765432"

    invalida = client.patch(f"{PREFIX}/clientes/me", json={"cedula": "12345"}, headers=headers)
    assert invalida.status_code == 400


def test_no_permite_tomar_cuenta_cambiando_el_celular(client):
    login_cliente(client, "TST501", "3001112233", "Titular")

    resp = client.post(
        f"{PREFIX}/auth/otp/request",
        json={"placa": "TST501", "telefono": "3999998888", "nombre": "Atacante"},
    )
    assert resp.status_code == 200, resp.text
    # El OTP viaja al numero ya registrado, no al que envia el atacante.
    assert resp.json()["telefono_parcial"] == "****2233"

    verify = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST501", "codigo": resp.json()["debug_codigo"]})
    assert verify.status_code == 200, verify.text
    assert verify.json()["cliente"]["telefono"] == "3001112233"
    assert verify.json()["cliente"]["nombre"] == "Titular"


def test_rate_limit_admin_no_se_salta_con_x_forwarded_for(client, monkeypatch):
    from app.config import settings
    from app.services import rate_limit

    rate_limit._memoria.clear()
    rate_limit._cliente = None
    rate_limit._inicializado = True
    monkeypatch.setattr(settings, "ADMIN_RATE_MAX", 2)

    malas = {"usuario": "admin", "password": "incorrecta"}
    assert client.post(f"{PREFIX}/auth/admin", json=malas, headers={"X-Forwarded-For": "1.1.1.1, 9.9.9.9"}).status_code == 401
    assert client.post(f"{PREFIX}/auth/admin", json=malas, headers={"X-Forwarded-For": "2.2.2.2, 9.9.9.9"}).status_code == 401
    # El primer valor del header es del cliente: no debe abrir un bucket nuevo.
    assert client.post(f"{PREFIX}/auth/admin", json=malas, headers={"X-Forwarded-For": "3.3.3.3, 9.9.9.9"}).status_code == 429


def test_password_vacia_no_autentica(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "")
    resp = client.post(f"{PREFIX}/auth/admin", json={"usuario": "admin", "password": ""})
    assert resp.status_code == 401, resp.text


def test_sync_rechaza_api_key_vacia(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "SYNC_API_KEY", "")
    venta = {
        "id_externo": "SYNC-KEY-VACIA",
        "volumen_litros": 10,
        "monto": 20000,
    }
    resp = client.post(f"{PREFIX}/sync/venta", json=venta, headers={"X-API-Key": ""})
    assert resp.status_code == 401, resp.text


def test_cambiar_password_admin_revoca_tokens(client, admin_headers, monkeypatch):
    from app.config import settings

    assert client.get(f"{PREFIX}/admin/resumen", headers=admin_headers).status_code == 200
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "otra-clave-larga-123")
    assert client.get(f"{PREFIX}/admin/resumen", headers=admin_headers).status_code == 401


def test_configuracion_insegura_falla_en_produccion(monkeypatch):
    from app.config import settings
    from app.security import validar_configuracion_produccion

    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "SECRET_KEY", "cambiar_por_openssl_rand_base64_48")
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "admin123")
    monkeypatch.setattr(settings, "SYNC_API_KEY", "dev-api-key")
    monkeypatch.setattr(settings, "CORS_ORIGINS", "*")
    monkeypatch.setattr(settings, "SMS_PROVIDER", "debug")

    try:
        validar_configuracion_produccion()
    except RuntimeError:
        pass
    else:
        raise AssertionError("La configuracion insegura deberia abortar el arranque")


def test_configuracion_segura_arranca_en_produccion(monkeypatch):
    from app.config import settings
    from app.security import validar_configuracion_produccion

    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 48)
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "clave-admin-segura")
    monkeypatch.setattr(settings, "SYNC_API_KEY", "clave-sync-de-32-caracteres-000001")
    monkeypatch.setattr(settings, "CORS_ORIGINS", "https://fidelizacion.megas.com.co")
    monkeypatch.setattr(settings, "SMS_PROVIDER", "http")

    validar_configuracion_produccion()
