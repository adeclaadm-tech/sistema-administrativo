"""Hash de contraseñas y emisión/verificación de JWT."""

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TipoToken = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(plano: str, hasheado: str) -> bool:
    return pwd_context.verify(plano, hasheado)


def crear_token(
    subject: str,
    *,
    tipo: TipoToken = "access",
    claims: dict[str, Any] | None = None,
    expira_en_minutos: int | None = None,
) -> str:
    if expira_en_minutos is None:
        expira_en_minutos = (
            settings.ACCESS_TOKEN_EXPIRE_MINUTES
            if tipo == "access"
            else settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    ahora = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": tipo,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=expira_en_minutos),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decodificar_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
