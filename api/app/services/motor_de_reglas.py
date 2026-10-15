from datetime import datetime
from decimal import ROUND_FLOOR, Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import Regla, utcnow


def regla_vigente(db: Session, ahora: datetime | None = None) -> Regla | None:
    momento = ahora or utcnow()
    return db.scalar(
        select(Regla)
        .where(
            Regla.activa.is_(True),
            or_(Regla.desde.is_(None), Regla.desde <= momento),
            or_(Regla.hasta.is_(None), Regla.hasta >= momento),
        )
        .order_by(Regla.prioridad.desc(), Regla.id.desc())
        .limit(1)
    )


def calcular_puntos(db: Session, litros, ahora: datetime | None = None) -> tuple[int, Regla | None]:
    regla = regla_vigente(db, ahora)
    if regla is None:
        return 0, None
    bruto = Decimal(str(litros)) * Decimal(regla.puntos_por_litro)
    puntos = int(bruto.to_integral_value(rounding=ROUND_FLOOR))
    return max(puntos, 0), regla
