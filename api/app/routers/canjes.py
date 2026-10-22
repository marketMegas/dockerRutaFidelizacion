from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_cliente
from ..models import Canje, Cliente
from ..schemas import CanjeIn
from ..services import catalogo, ledger, niveles
from ..services.motor_de_reglas import regla_vigente

router = APIRouter(tags=["canjes"])

MAX_INTENTOS_CANJE = 3


def _bloquear_cliente(db: Session, cliente_id: int) -> Cliente:
    """Toma el lock de la fila del cliente para serializar los canjes."""
    consulta = select(Cliente).where(Cliente.id == cliente_id)
    if db.bind is not None and db.bind.dialect.name != "sqlite":
        consulta = consulta.with_for_update()
    cliente = db.scalar(consulta)
    if cliente is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Cliente no valido")
    return cliente


@router.get("/config")
def config(db: Session = Depends(get_db)):
    regla = regla_vigente(db)
    return {
        "puntos_por_litro": float(regla.puntos_por_litro) if regla is not None else 0.0,
        "regla": regla.nombre if regla is not None else None,
        "niveles": catalogo.niveles(),
    }


@router.get("/catalogo")
def catalogo_publico(db: Session = Depends(get_db)):
    """Premios disponibles con cuantos codigos quedan. No expone los codigos."""
    premios = [p for p in catalogo.premios() if p["activo"]]
    conteo = catalogo.conteo_disponibles(db, premios)
    return {
        "version": catalogo.leer().get("version", 1),
        "premios": [
            {
                "clave": p["clave"],
                "nombre": p["nombre"],
                "descripcion": p["descripcion"],
                "imagen": p["imagen"],
                "costo_puntos": p["costo_puntos"],
                "codigos_disponibles": conteo.get(p["clave"], 0),
            }
            for p in premios
        ],
    }


@router.post("/canjes", status_code=status.HTTP_201_CREATED)
def crear_canje(
    body: CanjeIn,
    cliente: Cliente = Depends(require_cliente),
    db: Session = Depends(get_db),
):
    premio = catalogo.premio_por_clave(body.premio_clave)
    if premio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Premio no encontrado")
    if not premio["activo"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El premio no esta disponible")

    cliente_bloqueado = _bloquear_cliente(db, cliente.id)
    canje = None
    for _ in range(MAX_INTENTOS_CANJE):
        try:
            canje = ledger.realizar_canje(db, cliente_bloqueado, premio)
            db.commit()
            break
        except IntegrityError:
            # Dos canjes simultaneos se carried el mismo codigo: se reintenta.
            db.rollback()
            cliente_bloqueado = _bloquear_cliente(db, cliente.id)
        except ledger.LedgerError as exc:
            db.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if canje is None:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "No se pudo reservar un codigo. Intenta de nuevo")

    nivel = niveles.nivel_efectivo(db, cliente_bloqueado.id)
    return {
        "canje_id": canje.id,
        "codigo": canje.codigo,
        "premio": canje.premio_nombre,
        "premio_clave": canje.premio_clave,
        "puntos_costo": canje.puntos_costo,
        "saldo": cliente_bloqueado.puntos,
        "nivel": nivel["nivel"]["nombre"] if nivel["nivel"] else None,
    }


@router.get("/canjes/mis")
def mis_canjes(cliente: Cliente = Depends(require_cliente), db: Session = Depends(get_db)):
    canjes = db.scalars(
        select(Canje).where(Canje.cliente_id == cliente.id).order_by(Canje.id.desc()).limit(100)
    ).all()
    return [
        {
            "id": c.id,
            "premio_clave": c.premio_clave,
            "premio": c.premio_nombre,
            "codigo": c.codigo,
            "puntos_costo": c.puntos_costo,
            "created_at": c.created_at,
        }
        for c in canjes
    ]
