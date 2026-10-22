"""Niveles de fidelidad por consumo mensual.

El nivel de un cliente es derivado, no se guarda: se calcula con el consumo en
litros del mes en curso y del mes anterior, y se toma el mayor de los dos. Asi
el dia 1 del mes el cliente conserva el nivel que tenia y sube de inmediato en
cuanto su consumo cruza un umbral.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Venta
from . import catalogo
from .periodo import inicio_mes_anterior_utc, inicio_mes_utc


def consumo_litros(db: Session, cliente_id: int, desde: datetime, hasta: datetime | None = None) -> float:
    """Litros consumidos por un cliente desde `desde` (hasta `hasta`, si se indica)."""
    consulta = select(func.coalesce(func.sum(Venta.volumen_litros), 0)).where(
        Venta.cliente_id == cliente_id,
        Venta.created_at >= desde,
    )
    if hasta is not None:
        consulta = consulta.where(Venta.created_at < hasta)
    return float(db.scalar(consulta) or 0)


def consumos_por_cliente(db: Session, desde: datetime, hasta: datetime | None = None) -> dict[int, float]:
    """Litros consumidos por cada cliente desde `desde`."""
    consulta = select(Venta.cliente_id, func.coalesce(func.sum(Venta.volumen_litros), 0)).where(
        Venta.created_at >= desde,
    )
    if hasta is not None:
        consulta = consulta.where(Venta.created_at < hasta)
    consulta = consulta.group_by(Venta.cliente_id)
    return {int(cliente_id): float(total or 0) for cliente_id, total in db.execute(consulta).all()}


def nivel_por_litros(litros: float, niveles: list[dict] | None = None) -> dict:
    """Nivel que alcanza un consumo en litros y el siguiente nivel por subir."""
    escalera = niveles if niveles is not None else catalogo.niveles()
    if not escalera:
        return {"nivel": None, "siguiente": None}
    orden = sorted(escalera, key=lambda n: float(n["minimo"]))
    actual = orden[0]
    for nivel in orden:
        if float(litros) + 1e-9 >= float(nivel["minimo"]):
            actual = nivel
        else:
            break
    siguiente = next((n for n in orden if float(n["minimo"]) > float(actual["minimo"])), None)
    return {"nivel": actual, "siguiente": siguiente}


def calcular_nivel(litros_anterior: float, litros_actual: float, niveles: list[dict] | None = None) -> dict:
    """Nivel efectivo = MAX(nivel del mes anterior, nivel del mes en curso)."""
    escalera = niveles if niveles is not None else catalogo.niveles()
    por_anterior = nivel_por_litros(litros_anterior, escalera)
    por_actual = nivel_por_litros(litros_actual, escalera)
    if por_anterior["nivel"] is None or por_actual["nivel"] is None:
        return {
            "nivel": None,
            "siguiente": None,
            "multiplicador": 1.0,
            "minimo": 0.0,
            "litros_mes": float(litros_actual),
            "litros_mes_anterior": float(litros_anterior),
            "faltan_para_subir": 0.0,
            "faltan_para_mantener": 0.0,
        }

    # El mayor de los dos niveles manda; el siguiente se busca desde ese nivel.
    if float(por_anterior["nivel"]["minimo"]) >= float(por_actual["nivel"]["minimo"]):
        efectivo = por_anterior["nivel"]
    else:
        efectivo = por_actual["nivel"]
    orden = sorted(escalera, key=lambda n: float(n["minimo"]))
    siguiente = next((n for n in orden if float(n["minimo"]) > float(efectivo["minimo"])), None)
    minimo = float(efectivo["minimo"])
    return {
        "nivel": efectivo,
        "siguiente": siguiente,
        "multiplicador": float(efectivo["multiplicador"]),
        "minimo": minimo,
        "litros_mes": float(litros_actual),
        "litros_mes_anterior": float(litros_anterior),
        "faltan_para_subir": max(0.0, float(siguiente["minimo"]) - float(litros_actual)) if siguiente else 0.0,
        "faltan_para_mantener": max(0.0, minimo - float(litros_actual)),
    }


def nivel_efectivo(
    db: Session,
    cliente_id: int,
    ahora: datetime | None = None,
    litros_extra: float = 0.0,
) -> dict:
    """Nivel efectivo del cliente. `litros_extra` suma litros que aun no estan
    guardados (por ejemplo la venta que se esta procesando)."""
    niveles = catalogo.niveles()
    inicio_mes = inicio_mes_utc(ahora)
    inicio_anterior = inicio_mes_anterior_utc(ahora)
    litros_actual = consumo_litros(db, cliente_id, inicio_mes) + float(litros_extra)
    litros_anterior = consumo_litros(db, cliente_id, inicio_anterior, hasta=inicio_mes)
    return calcular_nivel(litros_anterior, litros_actual, niveles)
