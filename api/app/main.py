from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from .config import settings
from .database import SessionLocal, engine
from .models import Base, Regla
from .routers import admin, asistente, auth, canjes, clientes, islero, sync
from .security import validar_configuracion_produccion
from .services import catalogo


def _seed():
    db = SessionLocal()
    try:
        if db.scalar(select(func.count(Regla.id))) == 0:
            db.add(Regla(nombre="Base GLP", puntos_por_litro=1.00, prioridad=0))
        db.commit()
    finally:
        db.close()
    # El catalogo vive en un archivo: se crea desde la plantilla si no existe.
    catalogo.leer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    validar_configuracion_produccion()
    Base.metadata.create_all(bind=engine)
    _seed()
    yield


# La documentacion interactiva solo se publica en desarrollo.
_docs = (
    {"docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}
    if settings.DEBUG
    else {"docs_url": None, "redoc_url": None, "openapi_url": None}
)

app = FastAPI(title="Fidelizacion GLP", version="0.1.0", lifespan=lifespan, **_docs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefijo = settings.API_PREFIX
app.include_router(auth.router, prefix=prefijo)
app.include_router(clientes.router, prefix=prefijo)
app.include_router(islero.router, prefix=prefijo)
app.include_router(sync.router, prefix=prefijo)
app.include_router(canjes.router, prefix=prefijo)
app.include_router(asistente.router, prefix=prefijo)
app.include_router(admin.router, prefix=prefijo)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(f"{settings.API_PREFIX}/health")
def health_prefijo():
    return {"status": "ok", "prefix": settings.API_PREFIX}
