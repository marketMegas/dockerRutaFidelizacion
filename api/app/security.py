import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from .config import settings

ALGORITHM = "HS256"

# Valores de plantilla que NUNCA deben llegar a produccion.
_PLANTILLAS_SECRET_KEY = {
    "cambiar_por_openssl_rand_base64_48",
    "secretkeyReemplazarEnProduccion",
}


def utcnow() -> datetime:
    return datetime.now(UTC)


def comparar_seguro(valor: str | None, esperado: str | None) -> bool:
    """Compara secretos en tiempo constante y rechaza valores vacios."""
    if not valor or not esperado:
        return False
    return hmac.compare_digest(valor, esperado)


def huella_admin() -> str:
    """Huella de la password admin para invalidar tokens al cambiarla."""
    mensaje = f"admin:{settings.ADMIN_PASSWORD}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), mensaje, hashlib.sha256).hexdigest()[:16]


def validar_configuracion_produccion() -> None:
    """Falla el arranque si en produccion quedan valores inseguros por defecto."""
    if settings.DEBUG:
        return

    problemas: list[str] = []
    secret = settings.SECRET_KEY.strip()
    if secret in _PLANTILLAS_SECRET_KEY or len(secret) < 32:
        problemas.append("SECRET_KEY de plantilla o menor a 32 caracteres")
    if settings.ADMIN_PASSWORD in {"", "admin123"} or len(settings.ADMIN_PASSWORD) < 10:
        problemas.append("ADMIN_PASSWORD vacia, de plantilla o menor a 10 caracteres")
    if settings.SYNC_API_KEY in {"", "dev-api-key"} or len(settings.SYNC_API_KEY) < 16:
        problemas.append("SYNC_API_KEY vacia, de plantilla o menor a 16 caracteres")
    if settings.CORS_ORIGINS.strip() in {"", "*"}:
        problemas.append("CORS_ORIGINS debe listar los dominios permitidos")
    if (settings.SMS_PROVIDER or "").strip().lower() == "debug":
        problemas.append("SMS_PROVIDER no puede ser 'debug' en produccion")

    if problemas:
        detalle = "\n- ".join(problemas)
        raise RuntimeError(f"Configuracion insegura para produccion:\n- {detalle}")


def crear_token(sub: str, role: str, horas: int = 12, extra: dict | None = None) -> str:
    ahora = utcnow()
    payload = {"sub": str(sub), "role": role, "iat": ahora, "exp": ahora + timedelta(hours=horas)}
    if extra:
        payload.update(extra)
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
