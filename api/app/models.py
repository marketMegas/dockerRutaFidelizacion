from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cedula: Mapped[str | None] = mapped_column(String(15), unique=True, index=True, nullable=True)
    telefono: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    placa: Mapped[str | None] = mapped_column(String(10), unique=True, index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    puntos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    otp_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    otp_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    otp_placa_pendiente: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    movimientos: Mapped[list["LedgerPuntos"]] = relationship(back_populates="cliente")
    vehiculos: Mapped[list["Vehiculo"]] = relationship(back_populates="cliente")


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True, nullable=False)
    placa: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    cliente: Mapped["Cliente"] = relationship(back_populates="vehiculos")


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True, nullable=False)
    volumen_litros: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    puntos_otorgados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    placa: Mapped[str | None] = mapped_column(String(10), nullable=True)
    estacion_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    origen: Mapped[str] = mapped_column(String(20), default="simulador", nullable=False)
    regla_id: Mapped[int | None] = mapped_column(ForeignKey("reglas.id"), nullable=True)
    id_externo: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True, nullable=False)

    cliente: Mapped["Cliente"] = relationship()


class LedgerPuntos(Base):
    __tablename__ = "ledger_puntos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    saldo_resultante: Mapped[int] = mapped_column(Integer, nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(80), nullable=True)
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True, nullable=False)

    cliente: Mapped["Cliente"] = relationship(back_populates="movimientos")


class Regla(Base):
    __tablename__ = "reglas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    puntos_por_litro: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    prioridad: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    desde: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hasta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class Canje(Base):
    __tablename__ = "canjes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True, nullable=False)
    premio_clave: Mapped[str] = mapped_column(String(60), nullable=False)
    premio_nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    puntos_costo: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    cliente: Mapped["Cliente"] = relationship()
