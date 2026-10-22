from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Canje, Cliente, LedgerPuntos, Venta


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


def codigo_disponible(db: Session, premio: dict) -> str | None:
    """Primer codigo del premio que todavia no se ha entregado."""
    codigos = list(premio.get("codigos") or [])
    if not codigos:
        return None
    asignados = set(db.scalars(select(Canje.codigo).where(Canje.codigo.in_(codigos))).all())
    for codigo in codigos:
        if codigo not in asignados:
            return codigo
    return None


def realizar_canje(db: Session, cliente: Cliente, premio: dict) -> Canje:
    """Canjea un premio del catalogo y reserva su codigo para el cliente."""
    if not premio.get("activo", True):
        raise LedgerError("El premio no esta disponible")
    costo = int(premio["costo_puntos"])
    if cliente.puntos < costo:
        raise SaldoInsuficienteError("Puntos insuficientes para el canje")

    codigo = codigo_disponible(db, premio)
    if codigo is None:
        raise LedgerError("No hay codigos disponibles de este premio")

    canje = Canje(
        cliente_id=cliente.id,
        premio_clave=str(premio["clave"]),
        premio_nombre=str(premio["nombre"]),
        codigo=codigo,
        puntos_costo=costo,
    )
    db.add(canje)
    db.flush()
    _aplicar(
        db,
        cliente,
        -costo,
        "canje",
        referencia=f"canje:{canje.id}",
        motivo=f"Canje: {premio['nombre']}",
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
    if mov.tipo == "canje" and mov.referencia and mov.referencia.startswith("canje:"):
        # Al anular un canje el codigo vuelve al pool del catalogo.
        canje = db.get(Canje, int(mov.referencia.split(":", 1)[1]))
        if canje is not None:
            db.delete(canje)
    return _aplicar(db, cliente, -mov.cantidad, "reverso", referencia=f"reverso:{mov.id}", motivo=motivo)
