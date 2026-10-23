from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Cliente, Vehiculo, Venta
from ..schemas import VentaSync
from ..security import normalizar_placa, placa_valida
from ..services import ledger, niveles
from ..services.motor_de_reglas import calcular_puntos

router = APIRouter(prefix="/sync", tags=["sync"])


def _verificar_api_key(x_api_key: str) -> None:
    if x_api_key != settings.SYNC_API_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key invalida")


def _resolver_cliente(db: Session, body: VentaSync) -> tuple[Cliente, str]:
    placa = normalizar_placa(body.placa)
    if not placa_valida(placa):
        placa = ""

    # Produccion identifica la venta por placa: el vehiculo ya registrado
    # define el cliente dueno, aunque la venta traiga otro telefono.
    if placa:
        vehiculo = db.scalar(select(Vehiculo).where(Vehiculo.placa == placa))
        if vehiculo is not None:
            cliente = db.get(Cliente, vehiculo.cliente_id)
            if cliente is not None and cliente.activo:
                return cliente, placa

    if body.telefono:
        cliente = db.scalar(select(Cliente).where(Cliente.telefono == body.telefono))
        if cliente is not None and cliente.activo:
            return cliente, placa

    if placa:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Placa no registrada")
    if body.telefono:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Telefono no registrado")
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Se requiere placa o telefono")


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

    cliente, placa = _resolver_cliente(db, body)
    if placa:
        vehiculo = db.scalar(select(Vehiculo).where(Vehiculo.placa == placa))
        if vehiculo is None:
            db.add(Vehiculo(cliente_id=cliente.id, placa=placa))
            cliente.placa = placa
        elif vehiculo.cliente_id == cliente.id:
            vehiculo.activo = True
            cliente.placa = placa

    # El nivel se calcula con la venta ya incluida: si la carga cruza un
    # umbral, esa misma venta se paga con el multiplicador del nivel nuevo.
    nivel = niveles.nivel_efectivo(db, cliente.id, litros_extra=body.volumen_litros)
    puntos, regla = calcular_puntos(db, body.volumen_litros, nivel["multiplicador"])
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
        "nivel": nivel["nivel"]["nombre"] if nivel["nivel"] else None,
        "multiplicador": nivel["multiplicador"],
    }
