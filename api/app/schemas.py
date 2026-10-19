from datetime import datetime

from pydantic import BaseModel, Field


class IdentificarIn(BaseModel):
    placa: str = Field(min_length=1, max_length=20)


class OtpRequest(BaseModel):
    placa: str = Field(min_length=1, max_length=20)
    telefono: str | None = Field(default=None, min_length=7, max_length=20)
    nombre: str | None = Field(default=None, max_length=120)
    cedula: str | None = Field(default=None, min_length=5, max_length=15)


class OtpVerify(BaseModel):
    placa: str = Field(min_length=1, max_length=20)
    codigo: str


class AdminLogin(BaseModel):
    usuario: str
    password: str


class VentaSync(BaseModel):
    id_externo: str = Field(min_length=1, max_length=80)
    volumen_litros: float = Field(gt=0)
    monto: float = Field(ge=0)
    placa: str | None = None
    estacion_id: str | None = None
    origen: str = "zencillo"
    qr_payload: str | None = None
    telefono: str | None = None


class ReglaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    puntos_por_litro: float = Field(ge=0)
    activa: bool = True
    prioridad: int = 0
    desde: datetime | None = None
    hasta: datetime | None = None


class ReglaPatchIn(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    puntos_por_litro: float | None = Field(default=None, ge=0)
    activa: bool | None = None
    prioridad: int | None = None
    desde: datetime | None = None
    hasta: datetime | None = None


class RecompensaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    descripcion: str | None = None
    imagen: str | None = Field(default=None, max_length=500)
    costo_puntos: int = Field(gt=0)
    stock: int = Field(ge=0)
    activa: bool = True


class CanjeIn(BaseModel):
    recompensa_id: int


class ReversoIn(BaseModel):
    motivo: str = "reverso manual"
