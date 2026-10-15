from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Canje, Cliente, LedgerPuntos, Recompensa, Venta


class LedgerError(ValueError):
    pass


class SaldoInsuficienteError(LedgerError):
    pass


def _aplicar(
    db: Session,
    cliente: Cliente,
    cantidad: int,
    tipo: str,
    referencia: str | None = None,
    motivo: str | None = None,
) -> LedgerPuntos:
    nuevo_saldo = cliente.puntos + cantidad
    if nuevo_saldo < 0:
        raise SaldoInsuficienteError("Saldo de puntos insuficiente")
    cliente.puntos = nuevo_saldo
    mov = LedgerPuntos(
        cliente_id=cliente.id,
        tipo=tipo,
        cantidad=cantidad,
        saldo_resultante=nuevo_saldo,
        referencia=referencia,
        motivo=motivo,
    )
    db.add(mov)
    db.flush()
    return mov


def registrar_acumulacion(db: Session, cliente: Cliente, venta: Venta, puntos: int) -> LedgerPuntos:
    return _aplicar(
        db,
        cliente,
        puntos,
        "acumulacion",
        referencia=f"venta:{venta.id}",
        motivo=f"Consumo {venta.volumen_litros} L ({venta.origen})",
    )


def realizar_canje(db: Session, cliente: Cliente, recompensa: Recompensa) -> Canje:
    if not recompensa.activa:
        raise LedgerError("Recompensa inactiva")
    if recompensa.stock <= 0:
        raise LedgerError("Recompensa sin stock")
    if cliente.puntos < recompensa.costo_puntos:
        raise SaldoInsuficienteError("Puntos insuficientes para el canje")

    recompensa.stock -= 1
    canje = Canje(cliente_id=cliente.id, recompensa_id=recompensa.id, puntos_costo=recompensa.costo_puntos)
    db.add(canje)
    db.flush()
    _aplicar(
        db,
        cliente,
        -recompensa.costo_puntos,
        "canje",
        referencia=f"canje:{canje.id}",
        motivo=f"Canje: {recompensa.nombre}",
    )
    return canje


def reversar_movimiento(db: Session, mov_id: int, motivo: str) -> LedgerPuntos:
    mov = db.get(LedgerPuntos, mov_id)
    if mov is None:
        raise LedgerError("Movimiento no encontrado")
    if mov.tipo not in ("acumulacion", "canje"):
        raise LedgerError("Solo se pueden reversar acumulaciones o canjes")

    ya = db.scalar(select(LedgerPuntos).where(LedgerPuntos.referencia == f"reverso:{mov.id}"))
    if ya is not None:
        raise LedgerError("El movimiento ya fue reversado")

    cliente = db.get(Cliente, mov.cliente_id)
    return _aplicar(db, cliente, -mov.cantidad, "reverso", referencia=f"reverso:{mov.id}", motivo=motivo)
