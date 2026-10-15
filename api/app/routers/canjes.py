from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_cliente
from ..models import Canje, Cliente, Recompensa
from ..schemas import CanjeIn
from ..services import ledger

router = APIRouter(tags=["canjes"])


@router.get("/recompensas")
def listar_recompensas(db: Session = Depends(get_db)):
    recompensas = db.scalars(
        select(Recompensa).where(Recompensa.activa.is_(True)).order_by(Recompensa.costo_puntos.asc())
    ).all()
    return [
        {
            "id": r.id,
            "nombre": r.nombre,
            "descripcion": r.descripcion,
            "costo_puntos": r.costo_puntos,
            "stock": r.stock,
        }
        for r in recompensas
    ]


@router.post("/canjes", status_code=status.HTTP_201_CREATED)
def crear_canje(body: CanjeIn, cliente: Cliente = Depends(require_cliente), db: Session = Depends(get_db)):
    recompensa = db.get(Recompensa, body.recompensa_id)
    if recompensa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recompensa no encontrada")

    try:
        canje = ledger.realizar_canje(db, cliente, recompensa)
    except ledger.SaldoInsuficienteError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except ledger.LedgerError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    db.commit()
    return {
        "canje_id": canje.id,
        "recompensa": recompensa.nombre,
        "puntos_costo": canje.puntos_costo,
        "saldo": cliente.puntos,
        "estado": canje.estado,
    }


@router.get("/canjes/mis")
def mis_canjes(cliente: Cliente = Depends(require_cliente), db: Session = Depends(get_db)):
    canjes = db.scalars(
        select(Canje).where(Canje.cliente_id == cliente.id).order_by(Canje.id.desc()).limit(100)
    ).all()
    return [
        {
            "id": c.id,
            "recompensa_id": c.recompensa_id,
            "recompensa": c.recompensa.nombre if c.recompensa else None,
            "puntos_costo": c.puntos_costo,
            "estado": c.estado,
            "created_at": c.created_at,
        }
        for c in canjes
    ]
