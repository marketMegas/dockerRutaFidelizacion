from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import require_cliente
from ..models import Cliente
from ..schemas import AsistenteIn
from ..services import asistente, rate_limit

router = APIRouter(prefix="/asistente", tags=["asistente"])


@router.post("/consulta")
def consulta(
    body: AsistenteIn,
    cliente: Cliente = Depends(require_cliente),
    db: Session = Depends(get_db),
):
    mensaje = body.mensaje.strip()
    if not mensaje:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Escribe una pregunta")

    if not rate_limit.permitir(
        f"asistente:{cliente.id}",
        settings.ASISTENTE_RATE_MAX,
        settings.ASISTENTE_RATE_VENTANA,
    ):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Demasiadas consultas seguidas. Espera un momento e intenta de nuevo.",
        )

    historial = [item.model_dump() for item in body.historial]
    return asistente.responder(db, cliente, mensaje, historial)
