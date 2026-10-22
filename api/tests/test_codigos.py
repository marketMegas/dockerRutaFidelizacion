from app.services import catalogo
from tests.conftest import PREFIX, enviar_venta, login_cliente


def test_canje_entrega_un_codigo_texto(client):
    headers = login_cliente(client, "COD101", "3011112222", "Ana")
    # 150 L en el mes: nivel Plata (x1.25) -> 187 puntos; el cafe cuesta 100.
    enviar_venta(client, "C-001", 150.0, 300000, telefono="3011112222")

    resp = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert catalogo.normalizar_codigo(data["codigo"]) == data["codigo"]
    assert data["puntos_costo"] == 100
    assert data["saldo"] == 87
    assert data["nivel"] == "Plata"


def test_cada_canje_usa_un_codigo_distinto(client):
    headers = login_cliente(client, "COD102", "3011113333", "Beto")
    enviar_venta(client, "C-002", 400.0, 800000, telefono="3011113333")

    primero = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers).json()
    segundo = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers).json()
    assert primero["codigo"] != segundo["codigo"]


def test_el_catalogo_publico_descuenta_los_codigos_entregados(client):
    headers = login_cliente(client, "COD103", "3011114444", "Caro")
    enviar_venta(client, "C-003", 400.0, 800000, telefono="3011114444")

    antes = client.get(f"{PREFIX}/catalogo").json()
    cafe_antes = next(p for p in antes["premios"] if p["clave"] == "cafe")

    client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers)

    despues = client.get(f"{PREFIX}/catalogo").json()
    cafe_despues = next(p for p in despues["premios"] if p["clave"] == "cafe")
    assert cafe_despues["codigos_disponibles"] == cafe_antes["codigos_disponibles"] - 1


def test_el_panel_ve_el_codigo_entregado(client, admin_headers):
    headers = login_cliente(client, "COD104", "3011115555", "Dani")
    enviar_venta(client, "C-004", 400.0, 800000, telefono="3011115555")
    canje = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers).json()

    lista = client.get(f"{PREFIX}/admin/canjes", headers=admin_headers).json()
    assert len(lista) == 1
    assert lista[0]["codigo"] == canje["codigo"]
    assert lista[0]["premio"] == "Café gratis"
    assert "estado" not in lista[0]


def test_no_hay_estado_de_entrega(client, admin_headers):
    headers = login_cliente(client, "COD105", "3011116666", "Eva")
    enviar_venta(client, "C-005", 400.0, 800000, telefono="3011116666")
    canje = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers).json()

    resp = client.post(f"{PREFIX}/admin/canjes/{canje['canje_id']}/entregado", headers=admin_headers)
    assert resp.status_code == 404


def test_reverso_devuelve_el_codigo_al_pool(client, admin_headers):
    headers = login_cliente(client, "COD106", "3011117777", "Fede")
    enviar_venta(client, "C-006", 400.0, 800000, telefono="3011117777")
    canje = client.post(f"{PREFIX}/canjes", json={"premio_clave": "cafe"}, headers=headers).json()
    assert canje["codigo"]

    antes = next(p for p in client.get(f"{PREFIX}/catalogo").json()["premios"] if p["clave"] == "cafe")

    movimientos = client.get(f"{PREFIX}/clientes/me/movimientos", headers=headers).json()
    mov = next(m for m in movimientos if m["tipo"] == "canje")

    resp = client.post(
        f"{PREFIX}/admin/movimientos/{mov['id']}/reverso",
        json={"motivo": "canje anulado"},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text

    despues = next(p for p in client.get(f"{PREFIX}/catalogo").json()["premios"] if p["clave"] == "cafe")
    assert despues["codigos_disponibles"] == antes["codigos_disponibles"] + 1
    assert client.get(f"{PREFIX}/admin/canjes", headers=admin_headers).json() == []
