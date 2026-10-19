import os
from pathlib import Path

os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "test-secret-clave-larga-de-32-bytes-o-mas-0000"
os.environ["DATABASE_URL"] = "sqlite:///./test_fidelizacion.db"
os.environ["ADMIN_USER"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["SYNC_API_KEY"] = "test-key"
os.environ["API_PREFIX"] = "/fid-api"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402

DB_FILE = Path("test_fidelizacion.db")
PREFIX = "/fid-api"


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_headers(client):
    resp = client.post(f"{PREFIX}/auth/admin", json={"usuario": "admin", "password": "admin123"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def solicitar_otp(client, placa: str, telefono: str | None = None, nombre: str | None = None) -> str:
    body = {"placa": placa}
    if telefono:
        body["telefono"] = telefono
    if nombre:
        body["nombre"] = nombre
    resp = client.post(f"{PREFIX}/auth/otp/request", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()["debug_codigo"]


def login_cliente(client, placa: str, telefono: str | None = None, nombre: str | None = None) -> dict:
    codigo = solicitar_otp(client, placa, telefono, nombre)
    resp = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": placa, "codigo": codigo})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def enviar_venta(
    client,
    id_externo: str,
    litros: float,
    monto: float,
    telefono: str | None = None,
    qr_payload: str | None = None,
    placa: str | None = None,
):
    body = {
        "id_externo": id_externo,
        "volumen_litros": litros,
        "monto": monto,
        "estacion_id": "EDS-01",
        "origen": "test",
    }
    if placa:
        body["placa"] = placa
    if telefono:
        body["telefono"] = telefono
    if qr_payload:
        body["qr_payload"] = qr_payload
    return client.post(f"{PREFIX}/sync/venta", json=body, headers={"X-API-Key": "test-key"})
