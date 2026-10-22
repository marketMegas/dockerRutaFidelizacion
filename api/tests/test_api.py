from tests.conftest import PREFIX, enviar_venta, login_cliente, solicitar_otp


def test_flujo_completo(client, admin_headers):
    headers = login_cliente(client, "TST101", "3001112233", "Juan Perez")

    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert perfil.status_code == 200
    assert perfil.json()["placa"] == "TST101"
    assert perfil.json()["cedula"] == "3001112233"
    assert perfil.json()["telefono"] == "3001112233"
    assert perfil.json()["nivel"]["clave"] == "arranque"
    assert perfil.json()["multiplicador"] == 1.0
    assert [n["clave"] for n in perfil.json()["niveles"]] == ["arranque", "plata", "oro", "diamante"]

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

    catalogo = client.get(f"{PREFIX}/catalogo")
    assert catalogo.status_code == 200
    assert len(catalogo.json()["premios"]) >= 1

    movimientos = client.get(f"{PREFIX}/clientes/me/movimientos", headers=headers)
    assert movimientos.status_code == 200
    assert len(movimientos.json()) == 1


def test_sync_requiere_api_key(client):
    login_cliente(client, "TST104", "3007778899")
    resp = client.post(
        f"{PREFIX}/sync/venta",
        json={"id_externo": "F-NOKEY", "volumen_litros": 5, "monto": 10000, "telefono": "3007778899"},
        headers={"X-API-Key": "clave-mala"},
    )
    assert resp.status_code == 401


def test_sync_requiere_telefono(client):
    resp = client.post(
        f"{PREFIX}/sync/venta",
        json={"id_externo": "F-NOTEL", "volumen_litros": 5, "monto": 10000},
        headers={"X-API-Key": "test-key"},
    )
    assert resp.status_code == 400
    assert "telefono" in resp.json()["detail"]


def test_endpoint_qr_no_existe(client):
    assert client.get(f"{PREFIX}/clientes/me/qr").status_code == 404


def test_canje_y_reversion_admin(client, admin_headers):
    headers = login_cliente(client, "TST105", "3001234567", "Pedro")
    # 300 L en el mes: el nivel es Oro (x1.5), asi que la venta da 450 puntos.
    enviar_venta(client, "F-100", 300.0, 600000, telefono="3001234567")

    canje = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers)
    assert canje.status_code == 201, canje.text
    assert canje.json()["saldo"] == 350
    assert canje.json()["codigo"]
    assert canje.json()["premio"] == "Café gratis"
    assert canje.json()["nivel"] == "Oro"

    mis = client.get(f"{PREFIX}/canjes/mis", headers=headers)
    assert mis.status_code == 200
    assert len(mis.json()) == 1
    assert mis.json()[0]["codigo"] == canje.json()["codigo"]

    resumen = client.get(f"{PREFIX}/admin/resumen", headers=admin_headers)
    assert resumen.status_code == 200
    data = resumen.json()
    assert data["puntos_canjeados_mes"] == 100
    assert data["ventas_mes"]["cantidad"] >= 1
    assert data["codigos_entregados"] == 1


def test_admin_protegido(client):
    assert client.get(f"{PREFIX}/admin/resumen").status_code in (401, 403)
    assert client.get(f"{PREFIX}/admin/resumen", headers={"Authorization": "Bearer malo"}).status_code == 401


def test_otp_incorrecto(client):
    solicitar_otp(client, "TST106", "3000001111")
    resp = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST106", "codigo": "000000"})
    assert resp.status_code == 400


def test_placa_del_cliente(client, admin_headers):
    login_cliente(client, "TST107", "3006665555", "Raul")
    venta = enviar_venta(client, "F-PL-1", 12.5, 25000, telefono="3006665555", placa="abc456")
    assert venta.status_code == 200, venta.text

    lista = client.get(f"{PREFIX}/admin/clientes?q=abc456", headers=admin_headers)
    assert lista.status_code == 200
    assert lista.json()["total"] == 1
    assert lista.json()["clientes"][0]["placa"] == "ABC456"
    assert lista.json()["clientes"][0]["nivel"]["clave"] == "arranque"
    assert lista.json()["clientes"][0]["nivel"]["multiplicador"] == 1.0
    assert lista.json()["clientes"][0]["consumo_mes"] == 12.5

    detalle = client.get(
        f"{PREFIX}/admin/clientes/{lista.json()['clientes'][0]['id']}", headers=admin_headers
    )
    assert detalle.status_code == 200
    assert detalle.json()["cliente"]["placa"] == "ABC456"
    assert detalle.json()["cliente"]["nivel"]["clave"] == "arranque"


def test_sync_ignora_placa_invalida(client, admin_headers):
    headers = login_cliente(client, "TST108", "3005556677", "Luis")
    venta = enviar_venta(client, "F-PL-2", 10.0, 20000, telefono="3005556677", placa="ABC12D")
    assert venta.status_code == 200, venta.text

    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert perfil.json()["placa"] == "TST108"

    lista = client.get(f"{PREFIX}/admin/clientes?q=TST108", headers=admin_headers)
    detalle = client.get(
        f"{PREFIX}/admin/clientes/{lista.json()['clientes'][0]['id']}", headers=admin_headers
    )
    assert detalle.json()["ventas"][0]["placa"] is None


def test_config_publico(client, admin_headers):
    cfg = client.get(f"{PREFIX}/config")
    assert cfg.status_code == 200
    assert cfg.json()["puntos_por_litro"] == 1.0

    regla_id = _crear_regla(client, admin_headers, "Doble", puntos_por_litro=2.0, prioridad=100)
    cfg = client.get(f"{PREFIX}/config")
    assert cfg.json()["puntos_por_litro"] == 2.0
    assert cfg.json()["regla"] == "Doble"

    client.put(f"{PREFIX}/admin/reglas/{regla_id}", json={"activa": False}, headers=admin_headers)
    cfg = client.get(f"{PREFIX}/config")
    assert cfg.json()["puntos_por_litro"] == 0.0


def test_solo_una_regla_activa(client, admin_headers):
    [base_id] = _ids_activas(client, admin_headers)

    promo = _crear_regla(client, admin_headers, "Promo switch", puntos_por_litro=3.0)
    assert _ids_activas(client, admin_headers) == [promo]

    client.put(f"{PREFIX}/admin/reglas/{base_id}", json={"activa": True}, headers=admin_headers)
    assert _ids_activas(client, admin_headers) == [base_id]


def _crear_regla(client, admin_headers, nombre, **campos):
    body = {"nombre": nombre, "puntos_por_litro": 1.0, "prioridad": 0, "activa": True}
    body.update(campos)
    resp = client.post(f"{PREFIX}/admin/reglas", json=body, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _ids_activas(client, admin_headers):
    reglas = client.get(f"{PREFIX}/admin/reglas", headers=admin_headers).json()
    return [r["id"] for r in reglas if r["activa"]]


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


def test_sync_asocia_placa_nueva(client, admin_headers):
    headers = login_cliente(client, "TST109", "3009998877", "Nora")
    venta = enviar_venta(client, "F-ASOC-1", 15.0, 30000, telefono="3009998877", placa="tst110")
    assert venta.status_code == 200, venta.text

    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert set(perfil.json()["placas"]) == {"TST109", "TST110"}

    lista = client.get(f"{PREFIX}/admin/clientes?q=TST110", headers=admin_headers)
    assert lista.json()["total"] == 1
    assert lista.json()["clientes"][0]["placas"] == ["TST109", "TST110"]


def test_sync_no_roba_placa_de_otra_cuenta(client, admin_headers):
    a = login_cliente(client, "TST111", "3003334455", "A")
    b = login_cliente(client, "TST112", "3003334466", "B")
    enviar_venta(client, "F-ROBA-1", 10.0, 20000, telefono="3003334466", placa="TST111")

    perfil_a = client.get(f"{PREFIX}/clientes/me", headers=a)
    perfil_b = client.get(f"{PREFIX}/clientes/me", headers=b)
    assert perfil_a.json()["placas"] == ["TST111"]
    assert perfil_b.json()["placas"] == ["TST112"]


def test_admin_agrega_y_quita_placa(client, admin_headers):
    headers = login_cliente(client, "TST113", "3003334477", "C")
    cid = client.get(f"{PREFIX}/clientes/me", headers=headers).json()["id"]

    alta = client.post(
        f"{PREFIX}/admin/clientes/{cid}/vehiculos", json={"placa": "tst114"}, headers=admin_headers
    )
    assert alta.status_code == 201, alta.text
    assert alta.json()["placa"] == "TST114"

    detalle = client.get(f"{PREFIX}/admin/clientes/{cid}", headers=admin_headers).json()
    assert {v["placa"] for v in detalle["cliente"]["placas"]} == {"TST113", "TST114"}

    vid = next(v["id"] for v in detalle["cliente"]["placas"] if v["placa"] == "TST114")
    baja = client.delete(f"{PREFIX}/admin/clientes/{cid}/vehiculos/{vid}", headers=admin_headers)
    assert baja.status_code == 200

    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert perfil.json()["placas"] == ["TST113"]

    repetida = client.post(
        f"{PREFIX}/admin/clientes/{cid}/vehiculos", json={"placa": "TST113"}, headers=admin_headers
    )
    assert repetida.status_code == 409

    invalida = client.post(
        f"{PREFIX}/admin/clientes/{cid}/vehiculos", json={"placa": "AB12"}, headers=admin_headers
    )
    assert invalida.status_code == 400


def test_placa_quitada_se_reactiva_al_entrar(client, admin_headers):
    headers = login_cliente(client, "TST115", "3003334488", "D")
    cid = client.get(f"{PREFIX}/clientes/me", headers=headers).json()["id"]

    detalle = client.get(f"{PREFIX}/admin/clientes/{cid}", headers=admin_headers).json()
    vid = detalle["cliente"]["placas"][0]["id"]
    client.delete(f"{PREFIX}/admin/clientes/{cid}/vehiculos/{vid}", headers=admin_headers)

    assert client.post(f"{PREFIX}/auth/identificar", json={"placa": "TST115"}).json()["existe"] is False

    codigo = solicitar_otp(client, "TST115", "3003334488")
    verify = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": "TST115", "codigo": codigo})
    assert verify.status_code == 200, verify.text
    assert verify.json()["cliente"]["placas"] == ["TST115"]


def test_admin_actualiza_cedula(client, admin_headers):
    headers = login_cliente(client, "TST116", "3003334499", "E")
    cid = client.get(f"{PREFIX}/clientes/me", headers=headers).json()["id"]

    resp = client.patch(
        f"{PREFIX}/admin/clientes/{cid}", json={"cedula": "1098765433"}, headers=admin_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["cedula"] == "1098765433"

    otra = login_cliente(client, "TST117", "3003334500", "F")
    otra_cid = client.get(f"{PREFIX}/clientes/me", headers=otra).json()["id"]

    duplicada = client.patch(
        f"{PREFIX}/admin/clientes/{otra_cid}", json={"cedula": "1098765433"}, headers=admin_headers
    )
    assert duplicada.status_code == 409

    invalida = client.patch(
        f"{PREFIX}/admin/clientes/{otra_cid}", json={"cedula": "12345"}, headers=admin_headers
    )
    assert invalida.status_code == 400


def test_admin_canjes_busca_por_cedula(client, admin_headers):
    headers = login_cliente(client, "TST118", "3003334511", "G")
    enviar_venta(client, "F-CD-1", 300.0, 600000, telefono="3003334511")

    canje = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers)
    assert canje.status_code == 201, canje.text

    lista = client.get(f"{PREFIX}/admin/canjes?q=3003334511", headers=admin_headers)
    assert lista.status_code == 200
    assert len(lista.json()) == 1
    assert lista.json()[0]["cedula"] == "3003334511"
    assert lista.json()[0]["codigo"] == canje.json()["codigo"]

    vacio = client.get(f"{PREFIX}/admin/canjes?q=0000000000", headers=admin_headers)
    assert vacio.json() == []


