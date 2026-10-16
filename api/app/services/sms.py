import json
import logging
import urllib.request

from ..config import settings

logger = logging.getLogger("fidelizacion.sms")


def _mensaje(codigo: str) -> str:
    return f"Tu codigo de verificacion GasLP Puntos es {codigo}. Vence en {settings.OTP_TTL_SECONDS // 60} minutos."


def enviar_otp(telefono: str, codigo: str) -> None:
    proveedor = (settings.SMS_PROVIDER or "debug").lower()
    if proveedor == "debug":
        logger.info("OTP %s -> %s", telefono, codigo)
        return
    if proveedor in ("http", "webhook"):
        _enviar_http(telefono, codigo)
        return
    raise RuntimeError(f"Proveedor SMS no soportado: {settings.SMS_PROVIDER}")


def _enviar_http(telefono: str, codigo: str) -> None:
    if not settings.SMS_API_URL:
        raise RuntimeError("SMS_API_URL no configurada")
    cuerpo = json.dumps({"to": telefono, "from": settings.SMS_FROM, "text": _mensaje(codigo)}).encode()
    cabeceras = {"Content-Type": "application/json"}
    if settings.SMS_API_KEY:
        cabeceras["Authorization"] = f"Bearer {settings.SMS_API_KEY}"
    req = urllib.request.Request(settings.SMS_API_URL, data=cuerpo, headers=cabeceras, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()
