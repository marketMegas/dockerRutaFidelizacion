"""Corte de mes del programa de fidelizacion.

El corte es de calendario local (America/Bogota por defecto): el mes empieza
el dia 1 a las 00:00 hora de la estacion. Las ventas se guardan en UTC naive,
asi que aqui se traducen los limites a UTC naive para poder filtrar por
`ventas.created_at` directamente en SQL.
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..config import settings


def zona_estacion() -> ZoneInfo:
    try:
        return ZoneInfo(settings.TZ_ESTACION)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def ahora_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def ahora_local(ahora: datetime | None = None) -> datetime:
    """Instante actual en hora local de la estacion (naive, para agrupar)."""
    base = ahora or ahora_utc()
    if base.tzinfo is None:
        base = base.replace(tzinfo=UTC)
    return base.astimezone(zona_estacion()).replace(tzinfo=None)


def a_utc(local: datetime) -> datetime:
    """Traduce una fecha local naive de la estacion a UTC naive."""
    return local.replace(tzinfo=zona_estacion()).astimezone(UTC).replace(tzinfo=None)


def inicio_mes_local(ahora: datetime | None = None) -> datetime:
    local = ahora_local(ahora)
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def inicio_mes_anterior_local(ahora: datetime | None = None) -> datetime:
    local = ahora_local(ahora)
    primero = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return (primero - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def inicio_mes_utc(ahora: datetime | None = None) -> datetime:
    return a_utc(inicio_mes_local(ahora))


def inicio_mes_anterior_utc(ahora: datetime | None = None) -> datetime:
    return a_utc(inicio_mes_anterior_local(ahora))


def inicio_dia_utc(ahora: datetime | None = None) -> datetime:
    local = ahora_local(ahora)
    return a_utc(local.replace(hour=0, minute=0, second=0, microsecond=0))


def etiqueta_periodo(ahora: datetime | None = None) -> str:
    local = ahora_local(ahora)
    return f"{local.year:04d}-{local.month:02d}"
