import os
import tempfile
from pathlib import Path

os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "test-secret-clave-larga-de-32-bytes-o-mas-0000"
os.environ["DATABASE_URL"] = "sqlite:///./test_fidelizacion.db"
os.environ["ADMIN_USER"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["SYNC_API_KEY"] = "test-key"
os.environ["API_PREFIX"] = "/fid-api"
# El rate-limit del login admin es por IP; en pruebas todas comparten "testclient",
# asi que se sube el tope para no bloquear la suite.
os.environ["ADMIN_RATE_MAX"] = "100000"

# El catalogo se aislia en un archivo propio: las pruebas no tocan el de la app.
CATALOGO_TEST = Path(tempfile.gettempdir()) / "fidelizacion_catalogo_test.json"
os.environ["CATALOGO_PATH"] = str(CATALOGO_TEST)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.services import catalogo  # noqa: E402

DB_FILE = Path("test_fidelizacion.db")
PREFIX = "/fid-api"


@pytest.fixture(autouse=True)
def catalogo_limpio():
    """Cada prueba parte del catalogo de la plantilla."""
    if CATALOGO_TEST.exists():
        CATALOGO_TEST.unlink()
    catalogo.invalidar_cache()
    catalogo.leer()
    yield
    catalogo.invalidar_cache()


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


def solicitar_otp(
    client, placa: str, telefono: str | None = None, nombre: str | None = None, cedula: str | None = None
) -> str:
    body = {"placa": placa}
    if telefono:
        body["telefono"] = telefono
        # El registro exige cedula; se deriva del telefono para mantenerlo unico y estable.
        body["cedula"] = cedula or "".join(ch for ch in telefono if ch.isdigit())
    if nombre:
        body["nombre"] = nombre
    resp = client.post(f"{PREFIX}/auth/otp/request", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()["debug_codigo"]


def login_cliente(
    client, placa: str, telefono: str | None = None, nombre: str | None = None, cedula: str | None = None
) -> dict:
    codigo = solicitar_otp(client, placa, telefono, nombre, cedula)
    resp = client.post(f"{PREFIX}/auth/otp/verify", json={"placa": placa, "codigo": codigo})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def enviar_venta(
    client,
    id_externo: str,
    litros: float,
    monto: float,
    telefono: str | None = None,
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
    return client.post(f"{PREFIX}/sync/venta", json=body, headers={"X-API-Key": "test-key"})
