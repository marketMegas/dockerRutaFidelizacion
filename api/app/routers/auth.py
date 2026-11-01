from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import ip_cliente
from ..models import Cliente, Usuario, Vehiculo
from ..models import utcnow as utcnow_modelo
from ..schemas import AdminLogin, IdentificarIn, IsleroLogin, OtpRequest, OtpVerify
from ..security import (
    cedula_valida,
    comparar_seguro,
    crear_token,
    enmascarar_telefono,
    generar_otp,
    hash_otp,
    huella_admin,
    normalizar_cedula,
    normalizar_placa,
    placa_valida,
    utcnow,
    verify_password,
)
from ..services import rate_limit, sms

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_INTENTOS = 5
ADMIN_TOKEN_HORAS = 2
PLACA_MSG = "Placa invalida: usa 3 letras y 3 numeros (ej. ABC123)"
CEDULA_MSG = "Cedula invalida: ingresa solo numeros (6 a 10)"


def _vehiculo(db: Session, placa: str) -> Vehiculo | None:
    return db.scalar(select(Vehiculo).where(Vehiculo.placa == placa, Vehiculo.activo.is_(True)))


def _buscar(db: Session, placa: str) -> Cliente | None:
    vehiculo = _vehiculo(db, placa)
    return vehiculo.cliente if vehiculo is not None else None


def _placas(db: Session, cliente: Cliente) -> list[str]:
    return list(
        db.scalars(
            select(Vehiculo.placa)
            .where(Vehiculo.cliente_id == cliente.id, Vehiculo.activo.is_(True))
            .order_by(Vehiculo.id)
        ).all()
    )


def _client_ip(request: Request) -> str:
    # Detras del proxy la IP real llega en X-Forwarded-For; se toma el ultimo
    # valor (el que agrega el proxy) para no confiar en el que envia el cliente.
    return ip_cliente(request)


@router.post("/identificar")
def identificar(body: IdentificarIn, request: Request, db: Session = Depends(get_db)):
    placa = normalizar_placa(body.placa)
    if not placa_valida(placa):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, PLACA_MSG)

    ip = _client_ip(request)
    if not rate_limit.permitir(f"ident-ip:{ip}", settings.IDENT_IP_RATE_MAX, settings.OTP_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")
    if not rate_limit.permitir(f"ident:{placa}", settings.OTP_RATE_MAX, settings.OTP_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")

    cliente = _buscar(db, placa)
    if cliente is None or not cliente.activo:
        return {"existe": False, "telefono_parcial": None}
    return {"existe": True, "telefono_parcial": enmascarar_telefono(cliente.telefono)}


@router.post("/otp/request")
def otp_request(body: OtpRequest, request: Request, db: Session = Depends(get_db)):
    placa = normalizar_placa(body.placa)
    if not placa_valida(placa):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, PLACA_MSG)

    ip = _client_ip(request)
    if not rate_limit.permitir(f"otp-ip:{ip}", settings.OTP_IP_RATE_MAX, settings.OTP_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")
    if not rate_limit.permitir(f"otp:{placa}", settings.OTP_RATE_MAX, settings.OTP_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")

    cedula = normalizar_cedula(body.cedula) or None
    if cedula is not None and not cedula_valida(cedula):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, CEDULA_MSG)
    telefono_nuevo = (body.telefono or "").strip()
    nombre = (body.nombre or "").strip()

    vehiculo = _vehiculo(db, placa)
    cliente = vehiculo.cliente if vehiculo is not None else None
    nuevo_cliente = False
    placa_nueva = vehiculo is None

    if cliente is not None:
        if not cliente.activo:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cliente inactivo")
        # El OTP solo puede viajar al telefono ya registrado. Aceptar uno nuevo
        # aqui permitia tomar la cuenta ajena conociendo unicamente la placa.
        telefono_nuevo = ""
        if nombre and not cliente.nombre:
            cliente.nombre = nombre
    else:
        # Placa nueva: puede ser un cliente nuevo o una placa nueva de un celular ya registrado
        if telefono_nuevo:
            cliente = db.scalar(select(Cliente).where(Cliente.telefono == telefono_nuevo))
        if cliente is not None:
            if not cliente.activo:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Cliente inactivo")
            if nombre and not cliente.nombre:
                cliente.nombre = nombre
            if cedula is not None:
                if cliente.cedula is None:
                    en_uso = db.scalar(
                        select(Cliente).where(Cliente.cedula == cedula, Cliente.id != cliente.id)
                    )
                    if en_uso is not None:
                        raise HTTPException(status.HTTP_409_CONFLICT, "Esa cedula ya esta registrada")
                    cliente.cedula = cedula
                elif cliente.cedula != cedula:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT, "Esa cedula no coincide con la cuenta de este celular"
                    )
        else:
            if not telefono_nuevo:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes indicar tu numero de celular")
            if not cedula:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes indicar tu numero de cedula")
            if db.scalar(select(Cliente).where(Cliente.cedula == cedula)) is not None:
                raise HTTPException(status.HTTP_409_CONFLICT, "Esa cedula ya esta registrada")
            cliente = Cliente(cedula=cedula, telefono=telefono_nuevo, nombre=nombre)
            db.add(cliente)
            db.flush()
            nuevo_cliente = True
        cliente.otp_placa_pendiente = placa
        db.execute(
            update(Cliente)
            .where(Cliente.otp_placa_pendiente == placa, Cliente.id != cliente.id)
            .values(otp_placa_pendiente=None, otp_hash=None, otp_expires_at=None)
        )

    codigo = generar_otp()
    cliente.otp_hash = hash_otp(placa, codigo)
    cliente.otp_expires_at = utcnow().replace(tzinfo=None) + timedelta(seconds=settings.OTP_TTL_SECONDS)
    cliente.otp_attempts = 0
    db.commit()

    sms.enviar_otp(cliente.telefono, codigo)

    respuesta = {
        "ok": True,
        "cliente_nuevo": nuevo_cliente,
        "placa_nueva": placa_nueva,
        "telefono_parcial": enmascarar_telefono(cliente.telefono),
        "expira_en_segundos": settings.OTP_TTL_SECONDS,
    }
    if settings.DEBUG:
        respuesta["debug_codigo"] = codigo
    return respuesta


@router.post("/otp/verify")
def otp_verify(body: OtpVerify, db: Session = Depends(get_db)):
    placa = normalizar_placa(body.placa)
    if not placa_valida(placa):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, PLACA_MSG)

    vehiculo = _vehiculo(db, placa)
    if vehiculo is not None:
        cliente = vehiculo.cliente
    else:
        cliente = db.scalar(
            select(Cliente).where(Cliente.otp_placa_pendiente == placa, Cliente.otp_hash.is_not(None))
        )
    if cliente is None or cliente.otp_hash is None or not cliente.activo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hay codigo pendiente para esta placa")

    if cliente.otp_expires_at is None or cliente.otp_expires_at < utcnow().replace(tzinfo=None):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El codigo expiro, solicita uno nuevo")

    if cliente.otp_attempts >= MAX_INTENTOS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, solicita un nuevo codigo")

    if not comparar_seguro(hash_otp(placa, body.codigo), cliente.otp_hash):
        cliente.otp_attempts += 1
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Codigo incorrecto")

    if vehiculo is None:
        otro = db.scalar(select(Vehiculo).where(Vehiculo.placa == placa))
        if otro is not None and otro.cliente_id != cliente.id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Esa placa ya esta registrada en otra cuenta")
        if otro is None:
            db.add(Vehiculo(cliente_id=cliente.id, placa=placa))
        elif not otro.activo:
            otro.activo = True

    cliente.placa = placa
    cliente.otp_hash = None
    cliente.otp_expires_at = None
    cliente.otp_attempts = 0
    cliente.otp_placa_pendiente = None
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
            "placas": _placas(db, cliente),
        },
    }


@router.post("/admin")
def admin_login(body: AdminLogin, request: Request):
    ip = _client_ip(request)
    if not rate_limit.permitir(f"admin:{ip}", settings.ADMIN_RATE_MAX, settings.ADMIN_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")
    if not (
        comparar_seguro(body.usuario, settings.ADMIN_USER)
        and comparar_seguro(body.password, settings.ADMIN_PASSWORD)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")
    return {
        "access_token": crear_token(
            body.usuario,
            "admin",
            horas=ADMIN_TOKEN_HORAS,
            extra={"ver": huella_admin()},
        ),
        "token_type": "bearer",
        "rol": "admin",
        "nombre": "Administrador",
    }


@router.post("/islero")
def islero_login(body: IsleroLogin, request: Request, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    if not rate_limit.permitir(f"islero:{ip}", settings.ISLERO_RATE_MAX, settings.ISLERO_RATE_VENTANA):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Demasiados intentos, espera unos minutos")

    usuario = db.scalar(select(Usuario).where(Usuario.usuario == body.usuario))
    if usuario is None or not usuario.activo or not verify_password(body.password, usuario.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")

    usuario.ultimo_acceso = utcnow_modelo()
    db.commit()
    return {
        "access_token": crear_token(usuario.id, "islero"),
        "token_type": "bearer",
        "rol": "islero",
        "nombre": usuario.nombre or usuario.usuario,
    }
