import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from .config import settings

ALGORITHM = "HS256"


def utcnow() -> datetime:
    return datetime.now(UTC)


def crear_token(sub: str, role: str, horas: int = 12) -> str:
    ahora = utcnow()
    payload = {"sub": str(sub), "role": role, "iat": ahora, "exp": ahora + timedelta(hours=horas)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def generar_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def normalizar_cedula(valor: str | None) -> str:
    return "".join(ch for ch in (valor or "") if ch.isdigit())


def normalizar_placa(valor: str | None) -> str:
    return "".join(ch for ch in (valor or "").upper() if "A" <= ch <= "Z" or "0" <= ch <= "9")[:10]


def enmascarar_telefono(telefono: str | None) -> str:
    limpio = (telefono or "").strip()
    if len(limpio) <= 4:
        return "****"
    return "****" + limpio[-4:]


def hash_otp(identidad: str, codigo: str) -> str:
    msg = f"{identidad}:{codigo}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()


def firmar_qr(cliente_id: int) -> str:
    data = {
        "v": 1,
        "cid": cliente_id,
        "ts": int(utcnow().timestamp()),
        "nonce": secrets.token_urlsafe(8),
    }
    raw = json.dumps(data, separators=(",", ":"), sort_keys=True).encode()
    body = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    sig = hmac.new(settings.SECRET_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{body}.{sig}"


def verificar_qr(payload: str) -> dict:
    try:
        body, sig = payload.split(".", 1)
    except ValueError as exc:
        raise ValueError("QR invalido") from exc

    esperado = hmac.new(settings.SECRET_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, esperado):
        raise ValueError("Firma de QR invalida")

    pad = "=" * (-len(body) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(body + pad))
    except Exception as exc:
        raise ValueError("QR ilegible") from exc

    edad = int(utcnow().timestamp()) - int(data.get("ts", 0))
    if edad > settings.QR_TTL_SECONDS:
        raise ValueError("QR expirado")
    return data
