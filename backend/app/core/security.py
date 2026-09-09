"""Hash de contraseñas y emisión/verificación de JWT."""

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

TipoToken = Literal["access", "refresh"]

# bcrypt ignora todo lo que pase de 72 bytes. Se recorta explícitamente para que
# el hash y la verificación vean lo mismo en contraseñas largas o con acentos.
LIMITE_BCRYPT = 72


def _a_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:LIMITE_BCRYPT]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_a_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verificar_password(plano: str, hasheado: str) -> bool:
    try:
        return bcrypt.checkpw(_a_bytes(plano), hasheado.encode("utf-8"))
    except ValueError:
        # Hash corrupto o con un formato que bcrypt no reconoce: no es una
        # coincidencia, pero tampoco un 500.
        return False


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
