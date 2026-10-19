from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Cliente, Venta
from ..schemas import VentaSync
from ..security import normalizar_placa, verificar_qr
from ..services import ledger
from ..services.motor_de_reglas import calcular_puntos

router = APIRouter(prefix="/sync", tags=["sync"])


def _verificar_api_key(x_api_key: str) -> None:
    if x_api_key != settings.SYNC_API_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key invalida")


def _resolver_cliente(db: Session, body: VentaSync) -> Cliente:
    if body.qr_payload:
        try:
            data = verificar_qr(body.qr_payload)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
        cliente = db.get(Cliente, int(data["cid"]))
        if cliente is None or not cliente.activo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente del QR no existe")
        return cliente

    if body.telefono:
        cliente = db.scalar(select(Cliente).where(Cliente.telefono == body.telefono))
        if cliente is None or not cliente.activo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Telefono no registrado")
        return cliente

    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Se requiere qr_payload o telefono")


@router.post("/venta")
def sincronizar_venta(
    body: VentaSync,
    x_api_key: str = Header(default=""),
    db: Session = Depends(get_db),
):
    _verificar_api_key(x_api_key)

    existente = db.scalar(select(Venta).where(Venta.id_externo == body.id_externo))
    if existente is not None:
        cliente = db.get(Cliente, existente.cliente_id)
        return {
            "duplicado": True,
            "venta_id": existente.id,
            "puntos_otorgados": existente.puntos_otorgados,
            "saldo": cliente.puntos if cliente else None,
        }

    cliente = _resolver_cliente(db, body)
    placa = normalizar_placa(body.placa)
    if placa and placa != "SINPLACA":
        en_uso = db.scalar(
            select(Cliente).where(Cliente.placa == placa, Cliente.id != cliente.id)
        )
        if en_uso is None:
            cliente.placa = placa

    puntos, regla = calcular_puntos(db, body.volumen_litros)
    venta = Venta(
        cliente_id=cliente.id,
        volumen_litros=body.volumen_litros,
        monto=body.monto,
        puntos_otorgados=puntos,
        placa=placa or None,
        estacion_id=body.estacion_id,
        origen=body.origen,
        regla_id=regla.id if regla else None,
        id_externo=body.id_externo,
    )
    db.add(venta)
    db.flush()

    if puntos > 0:
        ledger.registrar_acumulacion(db, cliente, venta, puntos)

    db.commit()
    return {
        "duplicado": False,
        "venta_id": venta.id,
        "cliente_id": cliente.id,
        "puntos_otorgados": puntos,
        "saldo": cliente.puntos,
        "regla": regla.nombre if regla else None,
    }
