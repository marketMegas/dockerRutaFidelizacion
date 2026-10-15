from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Cliente
from ..schemas import AdminLogin, OtpRequest, OtpVerify
from ..security import crear_token, generar_otp, hash_otp, utcnow

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_INTENTOS = 5


@router.post("/otp/request")
def otp_request(body: OtpRequest, db: Session = Depends(get_db)):
    cliente = db.scalar(select(Cliente).where(Cliente.telefono == body.telefono))
    nuevo = cliente is None
    if cliente is None:
        cliente = Cliente(telefono=body.telefono, nombre=body.nombre or "")
        db.add(cliente)
        db.flush()
    elif body.nombre:
        cliente.nombre = body.nombre

    codigo = generar_otp()
    cliente.otp_hash = hash_otp(cliente.telefono, codigo)
    cliente.otp_expires_at = utcnow().replace(tzinfo=None) + timedelta(seconds=settings.OTP_TTL_SECONDS)
    cliente.otp_attempts = 0
    db.commit()

    respuesta = {
        "ok": True,
        "cliente_nuevo": nuevo,
        "expira_en_segundos": settings.OTP_TTL_SECONDS,
    }
    if settings.DEBUG:
        respuesta["debug_codigo"] = codigo
    return respuesta


@router.post("/otp/verify")
def otp_verify(body: OtpVerify, db: Session = Depends(get_db)):
    cliente = db.scalar(select(Cliente).where(Cliente.telefono == body.telefono))
    if cliente is None or cliente.otp_hash is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hay codigo pendiente para este telefono")

    if cliente.otp_expires_at is None or cliente.otp_expires_at < utcnow().replace(tzinfo=None):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El codigo expiro, solicita uno nuevo")

    if cliente.otp_attempts >= MAX_INTENTOS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, solicita un nuevo codigo")

    if hash_otp(cliente.telefono, body.codigo) != cliente.otp_hash:
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
        "cliente": {"id": cliente.id, "telefono": cliente.telefono, "nombre": cliente.nombre, "puntos": cliente.puntos},
    }


@router.post("/admin")
def admin_login(body: AdminLogin):
    if body.usuario != settings.ADMIN_USER or body.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")
    return {"access_token": crear_token(body.usuario, "admin"), "token_type": "bearer"}
