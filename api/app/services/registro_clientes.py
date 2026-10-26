from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import AuditoriaCliente, Cliente, Vehiculo
from ..security import (
    cedula_valida,
    normalizar_cedula,
    normalizar_placa,
    normalizar_telefono,
    placa_valida,
    telefono_valido,
)

PLACA_MSG = "Placa invalida: usa 3 letras y 3 numeros (ej. ABC123)"
CEDULA_MSG = "Cedula invalida: ingresa solo numeros (6 a 10)"
TELEFONO_MSG = "Celular invalido: ingresa 10 digitos"


class ErrorRegistro(Exception):
    def __init__(self, mensaje: str, estado: int = 400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.estado = estado


def _datos_cliente(cliente: Cliente) -> dict:
    return {
        "cedula": cliente.cedula,
        "telefono": cliente.telefono,
        "nombre": cliente.nombre,
    }


def _placas(db: Session, cliente: Cliente) -> list[str]:
    return list(
        db.scalars(
            select(Vehiculo.placa)
            .where(Vehiculo.cliente_id == cliente.id, Vehiculo.activo.is_(True))
            .order_by(Vehiculo.id)
        ).all()
    )


def _validar_cedula_unica(db: Session, cedula: str, cliente_id: int | None = None) -> None:
    consulta = select(Cliente).where(Cliente.cedula == cedula)
    if cliente_id is not None:
        consulta = consulta.where(Cliente.id != cliente_id)
    if db.scalar(consulta) is not None:
        raise ErrorRegistro("Esa cedula ya esta registrada", 409)


def _validar_telefono_unico(db: Session, telefono: str, cliente_id: int | None = None) -> None:
    consulta = select(Cliente).where(Cliente.telefono == telefono)
    if cliente_id is not None:
        consulta = consulta.where(Cliente.id != cliente_id)
    if db.scalar(consulta) is not None:
        raise ErrorRegistro("Ese celular ya esta registrado", 409)


def _validar_unicos(db: Session, cedula: str, telefono: str, cliente_id: int) -> None:
    _validar_cedula_unica(db, cedula, cliente_id)
    _validar_telefono_unico(db, telefono, cliente_id)


def consultar_por_placa(db: Session, valor_placa: str) -> dict:
    placa = normalizar_placa(valor_placa)
    if not placa_valida(placa):
        raise ErrorRegistro(PLACA_MSG, 400)

    vehiculo = db.scalar(select(Vehiculo).where(Vehiculo.placa == placa))
    if vehiculo is None:
        return {"existe": False, "cliente": None}

    cliente = db.get(Cliente, vehiculo.cliente_id)
    if cliente is None:
        return {"existe": False, "cliente": None}

    return {
        "existe": True,
        "cliente": {
            "id": cliente.id,
            "cedula": cliente.cedula,
            "telefono": cliente.telefono,
            "nombre": cliente.nombre,
            "activo": cliente.activo,
            "placas": _placas(db, cliente),
        },
    }


def registrar_cliente(
    db: Session,
    *,
    placa: str,
    cedula: str,
    telefono: str,
    nombre: str | None,
    usuario_id: int,
    ip: str | None = None,
) -> dict:
    placa = normalizar_placa(placa)
    if not placa_valida(placa):
        raise ErrorRegistro(PLACA_MSG, 400)

    cedula = normalizar_cedula(cedula)
    if not cedula_valida(cedula):
        raise ErrorRegistro(CEDULA_MSG, 400)

    telefono = normalizar_telefono(telefono)
    if not telefono_valido(telefono):
        raise ErrorRegistro(TELEFONO_MSG, 400)

    nombre = (nombre or "").strip()
    vehiculo = db.scalar(select(Vehiculo).where(Vehiculo.placa == placa))

    if vehiculo is not None:
        cliente = db.get(Cliente, vehiculo.cliente_id)
        if cliente is None:
            raise ErrorRegistro("La placa no tiene un cliente valido", 409)
        if not cliente.activo:
            raise ErrorRegistro("Cliente inactivo", 403)

        antes = _datos_cliente(cliente)
        _validar_unicos(db, cedula, telefono, cliente.id)
        vehiculo.activo = True
        cliente.cedula = cedula
        cliente.telefono = telefono
        if nombre:
            cliente.nombre = nombre
        cliente.placa = placa
        accion = "actualizar"
        creado = False
    else:
        cliente = db.scalar(select(Cliente).where(Cliente.telefono == telefono))
        if cliente is not None:
            if not cliente.activo:
                raise ErrorRegistro("Cliente inactivo", 403)

            antes = _datos_cliente(cliente)
            if cliente.cedula is None:
                _validar_cedula_unica(db, cedula, cliente.id)
                cliente.cedula = cedula
            elif cliente.cedula != cedula:
                raise ErrorRegistro("Esa cedula no coincide con la cuenta de este celular", 409)
            if nombre and not cliente.nombre:
                cliente.nombre = nombre
            db.add(Vehiculo(cliente_id=cliente.id, placa=placa))
            cliente.placa = placa
            accion = "actualizar"
            creado = False
        else:
            antes = None
            _validar_cedula_unica(db, cedula)
            cliente = Cliente(cedula=cedula, telefono=telefono, nombre=nombre)
            db.add(cliente)
            db.flush()
            db.add(Vehiculo(cliente_id=cliente.id, placa=placa))
            cliente.placa = placa
            accion = "crear"
            creado = True

    db.flush()
    auditoria = AuditoriaCliente(
        usuario_id=usuario_id,
        cliente_id=cliente.id,
        placa=placa,
        accion=accion,
        detalle={"antes": antes, "despues": _datos_cliente(cliente)},
        ip=(ip or "")[:45] or None,
    )
    db.add(auditoria)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ErrorRegistro("Ya existe un cliente con esos datos", 409) from exc

    db.refresh(cliente)
    return {
        "cliente_id": cliente.id,
        "placa": placa,
        "cedula": cliente.cedula,
        "telefono": cliente.telefono,
        "nombre": cliente.nombre,
        "creado": creado,
        "actualizado": not creado,
        "placas": _placas(db, cliente),
    }


def listar_registros(db: Session, usuario_id: int, limite: int = 20) -> list[dict]:
    registros = db.scalars(
        select(AuditoriaCliente)
        .where(AuditoriaCliente.usuario_id == usuario_id)
        .order_by(AuditoriaCliente.id.desc())
        .limit(min(max(limite, 1), 100))
    ).all()
    return [
        {
            "id": r.id,
            "cliente_id": r.cliente_id,
            "placa": r.placa,
            "accion": r.accion,
            "detalle": r.detalle,
            "ip": r.ip,
            "created_at": r.created_at,
        }
        for r in registros
    ]
