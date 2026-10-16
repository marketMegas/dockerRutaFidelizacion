from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Cliente
from ..schemas import AdminLogin, IdentificarIn, OtpRequest, OtpVerify
from ..security import crear_token, enmascarar_telefono, generar_otp, hash_otp, normalizar_cedula, utcnow
from ..services import rate_limit, sms

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_INTENTOS = 5
CEDULA_MIN = 6


def _buscar(db: Session, cedula: str) -> Cliente | None:
    return db.scalar(select(Cliente).where(Cliente.cedula == cedula))


@router.post("/identificar")
def identificar(body: IdentificarIn, db: Session = Depends(get_db)):
    cedula = normalizar_cedula(body.cedula)
    if not rate_limit.permitir(f"ident:{cedula}", settings.OTP_RATE_MAX, settings.OTP_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")

    cliente = _buscar(db, cedula)
    if cliente is None or not cliente.activo:
        return {"existe": False, "telefono_parcial": None}
    return {"existe": True, "telefono_parcial": enmascarar_telefono(cliente.telefono)}


@router.post("/otp/request")
def otp_request(body: OtpRequest, db: Session = Depends(get_db)):
    cedula = normalizar_cedula(body.cedula)
    if len(cedula) < CEDULA_MIN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cedula invalida")

    if not rate_limit.permitir(f"otp:{cedula}", settings.OTP_RATE_MAX, settings.OTP_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")

    cliente = _buscar(db, cedula)
    nuevo = cliente is None

    if nuevo:
        telefono = (body.telefono or "").strip()
        if not telefono:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes indicar tu numero de celular")
        if db.scalar(select(Cliente).where(Cliente.telefono == telefono)) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ese celular ya esta registrado")
        cliente = Cliente(cedula=cedula, telefono=telefono, nombre=(body.nombre or "").strip())
        db.add(cliente)
        db.flush()
    else:
        if not cliente.activo:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cliente inactivo")
        if body.nombre:
            cliente.nombre = body.nombre.strip()
        telefono_nuevo = (body.telefono or "").strip()
        if telefono_nuevo and telefono_nuevo != cliente.telefono:
            en_uso = db.scalar(
                select(Cliente).where(Cliente.telefono == telefono_nuevo, Cliente.id != cliente.id)
            )
            if en_uso is not None:
                raise HTTPException(status.HTTP_409_CONFLICT, "Ese celular ya esta registrado")
            cliente.telefono = telefono_nuevo

    codigo = generar_otp()
    cliente.otp_hash = hash_otp(cedula, codigo)
    cliente.otp_expires_at = utcnow().replace(tzinfo=None) + timedelta(seconds=settings.OTP_TTL_SECONDS)
    cliente.otp_attempts = 0
    db.commit()

    sms.enviar_otp(cliente.telefono, codigo)

    respuesta = {
        "ok": True,
        "cliente_nuevo": nuevo,
        "telefono_parcial": enmascarar_telefono(cliente.telefono),
        "expira_en_segundos": settings.OTP_TTL_SECONDS,
    }
    if settings.DEBUG:
        respuesta["debug_codigo"] = codigo
    return respuesta


@router.post("/otp/verify")
def otp_verify(body: OtpVerify, db: Session = Depends(get_db)):
    cedula = normalizar_cedula(body.cedula)
    cliente = _buscar(db, cedula)
    if cliente is None or cliente.otp_hash is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hay codigo pendiente para esta cedula")

    if cliente.otp_expires_at is None or cliente.otp_expires_at < utcnow().replace(tzinfo=None):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El codigo expiro, solicita uno nuevo")

    if cliente.otp_attempts >= MAX_INTENTOS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, solicita un nuevo codigo")

    if hash_otp(cedula, body.codigo) != cliente.otp_hash:
        cliente.otp_attempts += 1
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Codigo incorrecto")

    cliente.otp_hash = None
    cliente.otp_expires_at = None
    cliente.otp_attempts = 0
    db.commit()

    return {
        "access_token": crear_token(cliente.id, "cliente"),
        "token_type": "bearer",
        "cliente": {
            "id": cliente.id,
            "cedula": cliente.cedula,
            "telefono": cliente.telefono,
            "nombre": cliente.nombre,
            "puntos": cliente.puntos,
        },
    }


@router.post("/admin")
def admin_login(body: AdminLogin):
    if body.usuario != settings.ADMIN_USER or body.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")
    return {"access_token": crear_token(body.usuario, "admin"), "token_type": "bearer"}
