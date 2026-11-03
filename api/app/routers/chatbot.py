# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.deps import require_cliente
from app.models import Cliente
from app.services.chatbot.service import ChatbotService

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/message", response_model=schemas.ChatMessageOut)
def chatbot_message(
    body: schemas.ChatMessageIn,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(require_cliente),
):
    try:
        service = ChatbotService(db, cliente)
        result = service.procesar_mensaje(body.mensaje)
        return schemas.ChatMessageOut(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al procesar mensaje del chatbot")
