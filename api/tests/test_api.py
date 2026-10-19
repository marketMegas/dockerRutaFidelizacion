from tests.conftest import PREFIX, enviar_venta, login_cliente, solicitar_otp


def test_flujo_completo(client, admin_headers):
    headers = login_cliente(client, "TST101", "3001112233", "Juan Perez")

    perfil = client.get(f"{PREFIX}/clientes/me", headers=headers)
    assert perfil.status_code == 200
    assert perfil.json()["placa"] == "TST101"
    assert perfil.json()["cedula"] is None
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

    detalle = client.get(
        f"{PREFIX}/admin/clientes/{lista.json()['clientes'][0]['id']}", headers=admin_headers
    )
    assert detalle.status_code == 200
    assert detalle.json()["cliente"]["placa"] == "ABC456"


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
    assert cfg.json()["puntos_por_litro"] == 1.0


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


def test_recompensa_con_imagen(client, admin_headers):
    resp = client.post(
        f"{PREFIX}/admin/recompensas",
        json={
            "nombre": "Cafe con imagen",
            "descripcion": "Un cafe de la casa",
            "imagen": "https://cdn.ejemplo.com/cafe.jpg",
            "costo_puntos": 150,
            "stock": 5,
            "activa": True,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    recompensa_id = resp.json()["id"]

    admin = client.get(f"{PREFIX}/admin/recompensas", headers=admin_headers).json()
    creada = next(r for r in admin if r["id"] == recompensa_id)
    assert creada["imagen"] == "https://cdn.ejemplo.com/cafe.jpg"

    publicas = client.get(f"{PREFIX}/recompensas").json()
    publica = next(r for r in publicas if r["id"] == recompensa_id)
    assert publica["imagen"] == "https://cdn.ejemplo.com/cafe.jpg"


def test_recompensa_imagen_por_defecto(client, admin_headers):
    resp = client.post(
        f"{PREFIX}/admin/recompensas",
        json={"nombre": "Sin imagen", "costo_puntos": 80, "stock": 3, "activa": True},
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    recompensa_id = resp.json()["id"]

    admin = client.get(f"{PREFIX}/admin/recompensas", headers=admin_headers).json()
    creada = next(r for r in admin if r["id"] == recompensa_id)
    assert creada["imagen"] is None


def test_editar_imagen_recompensa(client, admin_headers):
    resp = client.post(
        f"{PREFIX}/admin/recompensas",
        json={
            "nombre": "Lavada con foto",
            "imagen": "https://cdn.ejemplo.com/antes.jpg",
            "costo_puntos": 200,
            "stock": 4,
            "activa": True,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    recompensa_id = resp.json()["id"]

    resp = client.put(
        f"{PREFIX}/admin/recompensas/{recompensa_id}",
        json={
            "nombre": "Lavada con foto",
            "imagen": "https://cdn.ejemplo.com/despues.jpg",
            "costo_puntos": 200,
            "stock": 4,
            "activa": True,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text

    admin = client.get(f"{PREFIX}/admin/recompensas", headers=admin_headers).json()
    editada = next(r for r in admin if r["id"] == recompensa_id)
    assert editada["imagen"] == "https://cdn.ejemplo.com/despues.jpg"


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


