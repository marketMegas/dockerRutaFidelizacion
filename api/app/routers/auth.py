from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Cliente
from ..schemas import AdminLogin, IdentificarIn, OtpRequest, OtpVerify
from ..security import (
    crear_token,
    enmascarar_telefono,
    generar_otp,
    hash_otp,
    normalizar_cedula,
    normalizar_placa,
    utcnow,
)
from ..services import rate_limit, sms

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_INTENTOS = 5
PLACA_MIN = 5


def _buscar(db: Session, placa: str) -> Cliente | None:
    return db.scalar(select(Cliente).where(Cliente.placa == placa))


@router.post("/identificar")
def identificar(body: IdentificarIn, db: Session = Depends(get_db)):
    placa = normalizar_placa(body.placa)
    if len(placa) < PLACA_MIN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Placa invalida")

    if not rate_limit.permitir(f"ident:{placa}", settings.OTP_RATE_MAX, settings.OTP_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")

    cliente = _buscar(db, placa)
    if cliente is None or not cliente.activo:
        return {"existe": False, "telefono_parcial": None}
    return {"existe": True, "telefono_parcial": enmascarar_telefono(cliente.telefono)}


@router.post("/otp/request")
def otp_request(body: OtpRequest, db: Session = Depends(get_db)):
    placa = normalizar_placa(body.placa)
    if len(placa) < PLACA_MIN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Placa invalida")

    if not rate_limit.permitir(f"otp:{placa}", settings.OTP_RATE_MAX, settings.OTP_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")

    cedula = normalizar_cedula(body.cedula) or None

    cliente = _buscar(db, placa)
    nuevo = cliente is None

    if nuevo:
        telefono = (body.telefono or "").strip()
        if not telefono:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes indicar tu numero de celular")
        if db.scalar(select(Cliente).where(Cliente.telefono == telefono)) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ese celular ya esta registrado")
        if cedula and db.scalar(select(Cliente).where(Cliente.cedula == cedula)) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Esa cedula ya esta registrada")
        cliente = Cliente(placa=placa, cedula=cedula, telefono=telefono, nombre=(body.nombre or "").strip())
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
    cliente.otp_hash = hash_otp(placa, codigo)
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
    placa = normalizar_placa(body.placa)
    cliente = _buscar(db, placa)
    if cliente is None or cliente.otp_hash is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hay codigo pendiente para esta placa")

    if cliente.otp_expires_at is None or cliente.otp_expires_at < utcnow().replace(tzinfo=None):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El codigo expiro, solicita uno nuevo")

    if cliente.otp_attempts >= MAX_INTENTOS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, solicita un nuevo codigo")

    if hash_otp(placa, body.codigo) != cliente.otp_hash:
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
            "placa": cliente.placa,
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
