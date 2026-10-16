from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Canje, Cliente, LedgerPuntos, Recompensa, Regla, Venta, utcnow
from ..schemas import RecompensaIn, ReglaIn, ReglaPatchIn, ReversoIn
from ..services import ledger

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/resumen")
def resumen(db: Session = Depends(get_db)):
    ahora = utcnow()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

    total_clientes = db.scalar(select(func.count(Cliente.id))) or 0
    clientes_nuevos_mes = db.scalar(select(func.count(Cliente.id)).where(Cliente.created_at >= inicio_mes)) or 0
    puntos_activos = db.scalar(select(func.coalesce(func.sum(Cliente.puntos), 0))) or 0

    acum_mes = db.scalar(
        select(func.coalesce(func.sum(LedgerPuntos.cantidad), 0)).where(
            LedgerPuntos.tipo == "acumulacion", LedgerPuntos.created_at >= inicio_mes
        )
    ) or 0
    canje_mes = db.scalar(
        select(func.coalesce(func.sum(LedgerPuntos.cantidad), 0)).where(
            LedgerPuntos.tipo == "canje", LedgerPuntos.created_at >= inicio_mes
        )
    ) or 0

    ventas_hoy = db.execute(
        select(
            func.count(Venta.id),
            func.coalesce(func.sum(Venta.volumen_litros), 0),
            func.coalesce(func.sum(Venta.monto), 0),
        ).where(Venta.created_at >= inicio_dia)
    ).one()

    ventas_mes = db.execute(
        select(
            func.count(Venta.id),
            func.coalesce(func.sum(Venta.volumen_litros), 0),
            func.coalesce(func.sum(Venta.monto), 0),
        ).where(Venta.created_at >= inicio_mes)
    ).one()

    return {
        "total_clientes": total_clientes,
        "clientes_nuevos_mes": clientes_nuevos_mes,
        "puntos_activos": int(puntos_activos),
        "puntos_acumulados_mes": int(acum_mes),
        "puntos_canjeados_mes": abs(int(canje_mes)),
        "ventas_hoy": {"cantidad": ventas_hoy[0], "litros": float(ventas_hoy[1]), "monto": float(ventas_hoy[2])},
        "ventas_mes": {"cantidad": ventas_mes[0], "litros": float(ventas_mes[1]), "monto": float(ventas_mes[2])},
    }


@router.get("/ventas")
def ventas_por_dia(dias: int = 14, db: Session = Depends(get_db)):
    dias = min(max(dias, 1), 90)
    desde = utcnow() - timedelta(days=dias)
    filas = db.execute(
        select(
            func.date(Venta.created_at).label("dia"),
            func.count(Venta.id),
            func.coalesce(func.sum(Venta.volumen_litros), 0),
            func.coalesce(func.sum(Venta.monto), 0),
            func.coalesce(func.sum(Venta.puntos_otorgados), 0),
        )
        .where(Venta.created_at >= desde)
        .group_by(func.date(Venta.created_at))
        .order_by(func.date(Venta.created_at))
    ).all()
    return [
        {"dia": str(f[0]), "cantidad": f[1], "litros": float(f[2]), "monto": float(f[3]), "puntos": int(f[4])}
        for f in filas
    ]


@router.get("/clientes")
def listar_clientes(q: str | None = None, limite: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    consulta = select(Cliente)
    if q:
        filtro = f"%{q}%"
        consulta = consulta.where(
            or_(
                Cliente.cedula.ilike(filtro),
                Cliente.telefono.ilike(filtro),
                Cliente.nombre.ilike(filtro),
                Cliente.placa.ilike(filtro),
            )
        )
    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    clientes = db.scalars(
        consulta.order_by(Cliente.puntos.desc()).limit(min(max(limite, 1), 200)).offset(max(offset, 0))
    ).all()
    return {
        "total": total,
        "clientes": [
            {
                "id": c.id,
                "cedula": c.cedula,
                "telefono": c.telefono,
                "nombre": c.nombre,
                "placa": c.placa,
                "puntos": c.puntos,
                "activo": c.activo,
                "created_at": c.created_at,
            }
            for c in clientes
        ],
    }


@router.get("/clientes/{cliente_id}")
def detalle_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")
    movimientos = db.scalars(
        select(LedgerPuntos).where(LedgerPuntos.cliente_id == cliente_id).order_by(LedgerPuntos.id.desc()).limit(200)
    ).all()
    ventas = db.scalars(
        select(Venta).where(Venta.cliente_id == cliente_id).order_by(Venta.id.desc()).limit(100)
    ).all()
    return {
        "cliente": {
            "id": cliente.id,
            "cedula": cliente.cedula,
            "telefono": cliente.telefono,
            "nombre": cliente.nombre,
            "placa": cliente.placa,
            "puntos": cliente.puntos,
        },
        "movimientos": [
            {
                "id": m.id,
                "tipo": m.tipo,
                "cantidad": m.cantidad,
                "saldo_resultante": m.saldo_resultante,
                "referencia": m.referencia,
                "motivo": m.motivo,
                "created_at": m.created_at,
            }
            for m in movimientos
        ],
        "ventas": [
            {
                "id": v.id,
                "id_externo": v.id_externo,
                "volumen_litros": float(v.volumen_litros),
                "monto": float(v.monto),
                "puntos_otorgados": v.puntos_otorgados,
                "placa": v.placa,
                "origen": v.origen,
                "created_at": v.created_at,
            }
            for v in ventas
        ],
    }


@router.post("/movimientos/{mov_id}/reverso")
def reversar(mov_id: int, body: ReversoIn, db: Session = Depends(get_db)):
    try:
        mov = ledger.reversar_movimiento(db, mov_id, body.motivo)
    except ledger.LedgerError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    db.commit()
    return {"reverso_id": mov.id, "cantidad": mov.cantidad, "saldo_resultante": mov.saldo_resultante}


@router.get("/canjes")
def listar_canjes(limite: int = 50, db: Session = Depends(get_db)):
    canjes = db.scalars(select(Canje).order_by(Canje.id.desc()).limit(min(max(limite, 1), 200))).all()
    return [
        {
            "id": c.id,
            "cliente_id": c.cliente_id,
            "cliente": c.cliente.nombre if c.cliente else None,
            "recompensa": c.recompensa.nombre if c.recompensa else None,
            "puntos_costo": c.puntos_costo,
            "estado": c.estado,
            "created_at": c.created_at,
        }
        for c in canjes
    ]


@router.post("/canjes/{canje_id}/entregado")
def marcar_entregado(canje_id: int, db: Session = Depends(get_db)):
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canje no encontrado")
    canje.estado = "entregado"
    db.commit()
    return {"canje_id": canje.id, "estado": canje.estado}


@router.get("/reglas")
def listar_reglas(db: Session = Depends(get_db)):
    reglas = db.scalars(select(Regla).order_by(Regla.prioridad.desc(), Regla.id.desc())).all()
    return [
        {
            "id": r.id,
            "nombre": r.nombre,
            "puntos_por_litro": float(r.puntos_por_litro),
            "activa": r.activa,
            "prioridad": r.prioridad,
            "desde": r.desde,
            "hasta": r.hasta,
        }
        for r in reglas
    ]


def _validar_rango(desde: datetime | None, hasta: datetime | None) -> None:
    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La fecha 'desde' no puede ser posterior a 'hasta'")


@router.post("/reglas", status_code=status.HTTP_201_CREATED)
def crear_regla(body: ReglaIn, db: Session = Depends(get_db)):
    existe = db.scalar(select(Regla).where(Regla.nombre == body.nombre))
    if existe is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una regla con ese nombre")
    _validar_rango(body.desde, body.hasta)
    regla = Regla(**body.model_dump())
    db.add(regla)
    db.commit()
    db.refresh(regla)
    return {"id": regla.id, "nombre": regla.nombre}


@router.put("/reglas/{regla_id}")
def actualizar_regla(regla_id: int, body: ReglaPatchIn, db: Session = Depends(get_db)):
    regla = db.get(Regla, regla_id)
    if regla is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regla no encontrada")

    datos = body.model_dump(exclude_unset=True)
    for campo in ("nombre", "puntos_por_litro", "activa", "prioridad"):
        if datos.get(campo) is None:
            datos.pop(campo, None)

    if "nombre" in datos:
        en_uso = db.scalar(select(Regla).where(Regla.nombre == datos["nombre"], Regla.id != regla_id))
        if en_uso is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una regla con ese nombre")

    _validar_rango(datos.get("desde", regla.desde), datos.get("hasta", regla.hasta))

    for campo, valor in datos.items():
        setattr(regla, campo, valor)
    db.commit()
    return {"id": regla.id, "nombre": regla.nombre, "activa": regla.activa}


@router.get("/recompensas")
def listar_recompensas_admin(db: Session = Depends(get_db)):
    recompensas = db.scalars(select(Recompensa).order_by(Recompensa.id.desc())).all()
    return [
        {
            "id": r.id,
            "nombre": r.nombre,
            "descripcion": r.descripcion,
            "imagen": r.imagen,
            "costo_puntos": r.costo_puntos,
            "stock": r.stock,
            "activa": r.activa,
        }
        for r in recompensas
    ]


@router.post("/recompensas", status_code=status.HTTP_201_CREATED)
def crear_recompensa(body: RecompensaIn, db: Session = Depends(get_db)):
    recompensa = Recompensa(**body.model_dump())
    db.add(recompensa)
    db.commit()
    db.refresh(recompensa)
    return {"id": recompensa.id, "nombre": recompensa.nombre}


@router.put("/recompensas/{recompensa_id}")
def actualizar_recompensa(recompensa_id: int, body: RecompensaIn, db: Session = Depends(get_db)):
    recompensa = db.get(Recompensa, recompensa_id)
    if recompensa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recompensa no encontrada")
    for campo, valor in body.model_dump().items():
        setattr(recompensa, campo, valor)
    db.commit()
    return {"id": recompensa.id, "nombre": recompensa.nombre, "activa": recompensa.activa}
