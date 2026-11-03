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


class IsleroLogin(BaseModel):
    usuario: str
    password: str


class RegistroIsleroIn(BaseModel):
    placa: str = Field(min_length=1, max_length=20)
    cedula: str = Field(min_length=1, max_length=15)
    telefono: str = Field(min_length=1, max_length=20)
    nombre: str | None = Field(default=None, max_length=120)


class IsleroCreate(BaseModel):
    usuario: str = Field(min_length=3, max_length=60)
    nombre: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=10, max_length=200)
    activo: bool = True


class IsleroPatch(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=10, max_length=200)
    activo: bool | None = None


class ClientePatchIn(BaseModel):
    cedula: str | None = Field(default=None, min_length=5, max_length=15)
    nombre: str | None = Field(default=None, max_length=120)


class VentaSync(BaseModel):
    id_externo: str = Field(min_length=1, max_length=80)
    volumen_litros: float = Field(gt=0)
    monto: float = Field(ge=0)
    placa: str | None = None
    estacion_id: str | None = None
    origen: str = "zencillo"
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


class NivelIn(BaseModel):
    clave: str = Field(min_length=1, max_length=60)
    nombre: str = Field(min_length=1, max_length=80)
    minimo: float = Field(ge=0)
    multiplicador: float = Field(gt=0)
    descripcion: str = ""


class PremioIn(BaseModel):
    clave: str = Field(min_length=1, max_length=60)
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = ""
    imagen: str = ""
    costo_puntos: int = Field(gt=0)
    activo: bool = True
    codigos: list[str] = Field(default_factory=list)


class CatalogoIn(BaseModel):
    version: int = 0
    niveles: list[NivelIn] = Field(default_factory=list)
    premios: list[PremioIn] = Field(default_factory=list)


class CanjeIn(BaseModel):
    premio_clave: str = Field(min_length=1, max_length=60)



class VehiculoIn(BaseModel):
    placa: str = Field(min_length=1, max_length=20)


class ReversoIn(BaseModel):
    motivo: str = "reverso manual"


class ChatMessageIn(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=500)


class ChatMessageOut(BaseModel):
    respuesta: str
    sugerencias: list[str] = []
