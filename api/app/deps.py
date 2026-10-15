from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Cliente
from .security import decodificar_token

bearer = HTTPBearer(auto_error=False)


def _payload(cred: HTTPAuthorizationCredentials | None) -> dict:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta token de acceso")
    try:
        return decodificar_token(cred.credentials)
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido o expirado") from exc


def require_admin(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    payload = _payload(cred)
    if payload.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol admin")
    return payload


def require_cliente(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Cliente:
    payload = _payload(cred)
    if payload.get("role") != "cliente":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol cliente")
    cliente = db.get(Cliente, int(payload["sub"]))
    if cliente is None or not cliente.activo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Cliente no valido")
    return cliente
