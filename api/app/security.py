import hashlib
import hmac
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


def placa_valida(valor: str | None) -> bool:
    placa = normalizar_placa(valor)
    return len(placa) == 6 and placa[:3].isalpha() and placa[3:].isdigit()


def enmascarar_telefono(telefono: str | None) -> str:
    limpio = (telefono or "").strip()
    if len(limpio) <= 4:
        return "****"
    return "****" + limpio[-4:]


def hash_otp(identidad: str, codigo: str) -> str:
    msg = f"{identidad}:{codigo}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()
