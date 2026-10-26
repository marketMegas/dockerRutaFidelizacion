from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_islero
from ..models import Usuario
from ..schemas import RegistroIsleroIn
from ..services import registro_clientes

router = APIRouter(prefix="/islero", tags=["islero"])


def _client_ip(request: Request) -> str:
    reenviado = request.headers.get("x-forwarded-for", "")
    if reenviado:
        return reenviado.split(",")[0].strip()
    return request.client.host if request.client else "desconocido"


def _http_error(exc: registro_clientes.ErrorRegistro) -> HTTPException:
    return HTTPException(exc.estado, exc.mensaje)


@router.get("/me")
def mi_perfil(usuario: Usuario = Depends(require_islero)):
    return {
        "id": usuario.id,
        "usuario": usuario.usuario,
        "nombre": usuario.nombre,
        "ultimo_acceso": usuario.ultimo_acceso,
    }


@router.get("/clientes")
def consultar_cliente(
    placa: str,
    usuario: Usuario = Depends(require_islero),
    db: Session = Depends(get_db),
):
    try:
        return registro_clientes.consultar_por_placa(db, placa)
    except registro_clientes.ErrorRegistro as exc:
        raise _http_error(exc) from exc


@router.post("/clientes")
def registrar_cliente(
    body: RegistroIsleroIn,
    request: Request,
    usuario: Usuario = Depends(require_islero),
    db: Session = Depends(get_db),
):
    try:
        return registro_clientes.registrar_cliente(
            db,
            placa=body.placa,
            cedula=body.cedula,
            telefono=body.telefono,
            nombre=body.nombre,
            usuario_id=usuario.id,
            ip=_client_ip(request),
        )
    except registro_clientes.ErrorRegistro as exc:
        raise _http_error(exc) from exc


@router.get("/registros")
def mis_registros(
    limite: int = 20,
    usuario: Usuario = Depends(require_islero),
    db: Session = Depends(get_db),
):
    return registro_clientes.listar_registros(db, usuario.id, limite)
