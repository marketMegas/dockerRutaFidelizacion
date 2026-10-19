from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_cliente
from ..models import Cliente, LedgerPuntos

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("/me")
def mi_perfil(cliente: Cliente = Depends(require_cliente)):
    return {
        "id": cliente.id,
        "cedula": cliente.cedula,
        "telefono": cliente.telefono,
        "nombre": cliente.nombre,
        "placa": cliente.placa,
        "email": cliente.email,
        "puntos": cliente.puntos,
        "created_at": cliente.created_at,
    }


@router.get("/me/movimientos")
def mis_movimientos(limite: int = 100, cliente: Cliente = Depends(require_cliente), db: Session = Depends(get_db)):
    movimientos = db.scalars(
        select(LedgerPuntos)
        .where(LedgerPuntos.cliente_id == cliente.id)
        .order_by(LedgerPuntos.id.desc())
        .limit(min(max(limite, 1), 500))
    ).all()
    return [
        {
            "id": m.id,
            "tipo": m.tipo,
            "cantidad": m.cantidad,
            "saldo_resultante": m.saldo_resultante,
            "referencia": m.referencia,
            "motivo": m.motivo,
            "created_at": m.created_at,
        }
        for m in movimientos
    ]
