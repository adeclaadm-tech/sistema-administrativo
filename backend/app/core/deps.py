"""Dependencias compartidas: sesión de base de datos y usuario autenticado.

Los cuatro guardas de rol se usan como dependencia en cada router:

    usuario_actual        -> cualquiera con token válido
    solo_afiliado         -> el portal de afiliados
    solo_admin            -> el panel (administrador y consultor)
    solo_administrador    -> acciones que escriben (aprobar, registrar pago, crear staff)
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decodificar_token
from app.db.session import get_db
from app.models.enums import RolUsuario, SubRolAdmin
from app.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

DbSession = Annotated[Session, Depends(get_db)]


def usuario_actual(
    db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> Usuario:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No pudimos validar tu sesión. Vuelve a iniciar sesión.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_token(token)
    if payload is None or payload.get("type") != "access":
        raise credenciales_invalidas

    sub = payload.get("sub")
    if not sub:
        raise credenciales_invalidas
    try:
        usuario_id = uuid.UUID(sub)
    except ValueError:
        raise credenciales_invalidas

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise credenciales_invalidas
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta cuenta está desactivada. Escríbele al equipo de ADECLA.",
        )
    return usuario


UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]


def solo_afiliado(usuario: UsuarioActual) -> Usuario:
    if usuario.rol != RolUsuario.AFILIADO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta ruta es del portal de afiliados.",
        )
    return usuario


def solo_admin(usuario: UsuarioActual) -> Usuario:
    if usuario.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Necesitas una cuenta del panel administrativo.",
        )
    return usuario


def solo_administrador(usuario: UsuarioActual) -> Usuario:
    """Bloquea al consultor: puede leer y exportar, no modificar."""
    if usuario.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Necesitas una cuenta del panel administrativo.",
        )
    if usuario.sub_rol != SubRolAdmin.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu perfil es de consulta. Esta acción la hace un administrador.",
        )
    return usuario


Afiliado_ = Annotated[Usuario, Depends(solo_afiliado)]
Admin = Annotated[Usuario, Depends(solo_admin)]
Administrador = Annotated[Usuario, Depends(solo_administrador)]
