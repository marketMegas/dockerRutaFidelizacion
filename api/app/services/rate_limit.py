import logging
import threading
import time

import redis

from ..config import settings

logger = logging.getLogger("fidelizacion.rate_limit")

_cliente: redis.Redis | None = None
_inicializado = False
_memoria: dict[str, list[float]] = {}
_memoria_lock = threading.Lock()
# Tope de claves en el fallback en memoria para que no crezca sin control.
_MAX_CLAVES_MEMORIA = 20_000
_HORIZONTE_MEMORIA = 3_600


def _obtener() -> redis.Redis | None:
    global _cliente, _inicializado
    if not _inicializado:
        _inicializado = True
        if settings.REDIS_URL:
            try:
                _cliente = redis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as exc:
                logger.warning("Redis no disponible, usando fallback en memoria: %s", exc)
                _cliente = None
        else:
            _cliente = None
    return _cliente


def _purgar_memoria(ahora: float) -> None:
    """Descarta claves sin actividad reciente (se llama con el lock tomado)."""
    limite = ahora - _HORIZONTE_MEMORIA
    for clave in list(_memoria):
        eventos = [t for t in _memoria.get(clave, []) if t >= limite]
        if eventos:
            _memoria[clave] = eventos
        else:
            _memoria.pop(clave, None)


def _permitir_memoria(clave: str, maximo: int, ventana: int) -> bool:
    ahora = time.monotonic()
    limite = ahora - ventana
    with _memoria_lock:
        eventos = [t for t in _memoria.get(clave, []) if t >= limite]
        if len(eventos) >= maximo:
            _memoria[clave] = eventos
            return False
        eventos.append(ahora)
        _memoria[clave] = eventos
        if len(_memoria) > _MAX_CLAVES_MEMORIA:
            _purgar_memoria(ahora)
            while len(_memoria) > _MAX_CLAVES_MEMORIA:
                _memoria.pop(next(iter(_memoria)))
        return True


def permitir(clave: str, maximo: int, ventana: int) -> bool:
    cliente = _obtener()
    if cliente is None:
        return _permitir_memoria(clave, maximo, ventana)
    try:
        total = cliente.incr(clave)
        if total == 1:
            cliente.expire(clave, ventana)
        return total <= maximo
    except Exception as exc:
        logger.warning("Fallo el rate-limit con Redis, usando fallback en memoria: %s", exc)
        return _permitir_memoria(clave, maximo, ventana)
