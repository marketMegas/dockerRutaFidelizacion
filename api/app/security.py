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


def normalizar_telefono(valor: str | None) -> str:
    digitos = "".join(ch for ch in (valor or "") if ch.isdigit())
    if len(digitos) == 12 and digitos.startswith("57"):
        return digitos[2:]
    return digitos


def telefono_valido(valor: str | None) -> bool:
    return len(normalizar_telefono(valor)) == 10


def normalizar_cedula(valor: str | None) -> str:
    return "".join(ch for ch in (valor or "") if ch.isdigit())


def cedula_valida(valor: str | None) -> bool:
    cedula = normalizar_cedula(valor)
    return 6 <= len(cedula) <= 10


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


_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derivada = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return f"scrypt${salt.hex()}${derivada.hex()}"


def verify_password(password: str, almacenado: str | None) -> bool:
    if not almacenado:
        return False
    try:
        algoritmo, salt_hex, hash_hex = almacenado.split("$", 2)
        if algoritmo != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        esperado = bytes.fromhex(hash_hex)
    except ValueError:
        return False

    derivada = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=len(esperado),
    )
    return hmac.compare_digest(derivada, esperado)
