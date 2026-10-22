from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_cliente
from ..models import Cliente, LedgerPuntos, Vehiculo
from ..schemas import ClientePatchIn
from ..security import cedula_valida, normalizar_cedula
from ..services import catalogo, niveles

router = APIRouter(prefix="/clientes", tags=["clientes"])

CEDULA_MSG = "Cedula invalida: ingresa solo numeros (6 a 10)"


def _perfil(db: Session, cliente: Cliente) -> dict:
    placas = list(
        db.scalars(
            select(Vehiculo.placa)
            .where(Vehiculo.cliente_id == cliente.id, Vehiculo.activo.is_(True))
            .order_by(Vehiculo.id)
        ).all()
    )
    nivel = niveles.nivel_efectivo(db, cliente.id)
    siguiente = nivel["siguiente"]
    actual = nivel["nivel"]
    return {
        "id": cliente.id,
        "cedula": cliente.cedula,
        "telefono": cliente.telefono,
        "nombre": cliente.nombre,
        "placa": cliente.placa,
        "placas": placas,
        "email": cliente.email,
        "puntos": cliente.puntos,
        "created_at": cliente.created_at,
        "nivel": (
            {
                "clave": actual["clave"],
                "nombre": actual["nombre"],
                "minimo": actual["minimo"],
                "multiplicador": actual["multiplicador"],
            }
            if actual
            else None
        ),
        "multiplicador": nivel["multiplicador"],
        "consumo_mes": nivel["litros_mes"],
        "consumo_mes_anterior": nivel["litros_mes_anterior"],
        "siguiente_nivel": (
            {"clave": siguiente["clave"], "nombre": siguiente["nombre"], "minimo": siguiente["minimo"]}
            if siguiente
            else None
        ),
        "faltan_para_subir": nivel["faltan_para_subir"],
        "faltan_para_mantener": nivel["faltan_para_mantener"],
        "niveles": catalogo.niveles(),
    }


@router.get("/me")
def mi_perfil(cliente: Cliente = Depends(require_cliente), db: Session = Depends(get_db)):
    return _perfil(db, cliente)


@router.patch("/me")
def actualizar_perfil(
    body: ClientePatchIn,
    cliente: Cliente = Depends(require_cliente),
    db: Session = Depends(get_db),
):
    if body.nombre is not None:
        nombre = body.nombre.strip()
        if nombre:
            cliente.nombre = nombre
    if body.cedula is not None:
        cedula = normalizar_cedula(body.cedula)
        if not cedula_valida(cedula):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, CEDULA_MSG)
        if cedula != cliente.cedula:
            en_uso = db.scalar(select(Cliente).where(Cliente.cedula == cedula, Cliente.id != cliente.id))
            if en_uso is not None:
                raise HTTPException(status.HTTP_409_CONFLICT, "Esa cedula ya esta registrada")
            cliente.cedula = cedula
    db.commit()
    db.refresh(cliente)
    return _perfil(db, cliente)


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
