import logging

import redis

from ..config import settings

logger = logging.getLogger("fidelizacion.rate_limit")

_cliente: redis.Redis | None = None
_inicializado = False


def _obtener() -> redis.Redis | None:
    global _cliente, _inicializado
    if not _inicializado:
        _inicializado = True
        if settings.REDIS_URL:
            try:
                _cliente = redis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as exc:
                logger.warning("Redis no disponible, rate-limit desactivado: %s", exc)
                _cliente = None
    return _cliente


def permitir(clave: str, maximo: int, ventana: int) -> bool:
    cliente = _obtener()
    if cliente is None:
        return True
    try:
        total = cliente.incr(clave)
        if total == 1:
            cliente.expire(clave, ventana)
        return total <= maximo
    except Exception as exc:
        logger.warning("Fallo el rate-limit, se permite la peticion: %s", exc)
        return True
