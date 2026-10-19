from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from .config import settings
from .database import SessionLocal, engine
from .models import Base, Recompensa, Regla
from .routers import admin, auth, canjes, clientes, sync


def _seed():
    db = SessionLocal()
    try:
        if db.scalar(select(func.count(Regla.id))) == 0:
            db.add(Regla(nombre="Base GLP", puntos_por_litro=1.00, prioridad=0))
        if db.scalar(select(func.count(Recompensa.id))) == 0:
            db.add(Recompensa(nombre="Cafe gratis", descripcion="Un cafe en tienda", costo_puntos=100, stock=100))
            db.add(Recompensa(nombre="Lavada basica", descripcion="Lavado express", costo_puntos=250, stock=50))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed()
    yield


app = FastAPI(title="Fidelizacion GLP", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefijo = settings.API_PREFIX
app.include_router(auth.router, prefix=prefijo)
app.include_router(clientes.router, prefix=prefijo)
app.include_router(sync.router, prefix=prefijo)
app.include_router(canjes.router, prefix=prefijo)
app.include_router(admin.router, prefix=prefijo)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(f"{settings.API_PREFIX}/health")
def health_prefijo():
    return {"status": "ok", "prefix": settings.API_PREFIX}
