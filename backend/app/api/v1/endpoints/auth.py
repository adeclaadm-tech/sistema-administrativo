"""Autenticación.

El registro abierto crea solo cuentas de afiliado. Las del panel se dan de
alta desde `/usuarios`, con sesión de administrador.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_, select

from app.core.config import settings
from app.core.deps import DbSession, UsuarioActual
from app.core.security import crear_token, decodificar_token, hash_password, verificar_password
from app.models.afiliado import Afiliado
from app.models.enums import EstadoAfiliado, RolUsuario
from app.models.usuario import Usuario
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegistroAfiliadoRequest,
    TokenPair,
)
from app.schemas.usuario import CambiarPassword, UsuarioOut
from app.schemas.common import Mensaje

router = APIRouter(prefix="/auth", tags=["auth"])

CREDENCIALES = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Correo, usuario, RNC o contraseña incorrectos.",
    headers={"WWW-Authenticate": "Bearer"},
)


def _buscar_usuario(db, identificador: str) -> Usuario | None:
    """Acepta correo, nombre de usuario o RNC.

    El representante de una constructora no siempre recuerda con qué correo lo
    dieron de alta, pero sí su usuario o el RNC de la empresa.
    """
    ident = identificador.strip().lower()

    usuario = db.scalar(select(Usuario).where(func.lower(Usuario.email) == ident))
    if usuario:
        return usuario

    usuario = db.scalar(select(Usuario).where(func.lower(Usuario.usuario) == ident))
    if usuario:
        return usuario
    afiliado = db.scalar(
        select(Afiliado).where(
            or_(Afiliado.rnc_cedula == identificador.strip(), func.lower(Afiliado.email) == ident)
        )
    )
    return afiliado.usuario if afiliado else None


def _emitir(db, usuario: Usuario) -> TokenPair:
    afiliado_id = usuario.afiliado.id if usuario.afiliado else None
    claims = {
        "rol": usuario.rol.value,
        "sub_rol": usuario.sub_rol.value if usuario.sub_rol else None,
        "email": usuario.email,
    }
    return TokenPair(
        access_token=crear_token(str(usuario.id), tipo="access", claims=claims),
        refresh_token=crear_token(str(usuario.id), tipo="refresh"),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        usuario=UsuarioOut.model_validate(usuario),
        afiliado_id=afiliado_id,
    )


@router.post("/login", response_model=TokenPair, summary="Login por JSON")
def login(datos: LoginRequest, db: DbSession) -> TokenPair:
    usuario = _buscar_usuario(db, datos.identificador)
    if usuario is None or not verificar_password(datos.password, usuario.password_hash):
        raise CREDENCIALES
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta cuenta está desactivada. Escríbele al equipo de ADECLA.",
        )
    return _emitir(db, usuario)


@router.post("/token", response_model=TokenPair, summary="Login OAuth2 (Swagger)")
def login_oauth2(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
) -> TokenPair:
    return login(LoginRequest(identificador=form.username, password=form.password), db)


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
    summary="Auto-registro de afiliado",
)
def registrar(datos: RegistroAfiliadoRequest, db: DbSession) -> TokenPair:
    email = datos.email.lower()
    if db.scalar(select(Usuario).where(func.lower(Usuario.email) == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con este correo.",
        )
    if db.scalar(select(Afiliado).where(Afiliado.rnc_cedula == datos.rnc_cedula)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este RNC ya está registrado. Recupera tu contraseña o escríbele a ADECLA.",
        )

    if datos.usuario:
        nombre_usuario = datos.usuario.strip().lower()
        if db.scalar(select(Usuario).where(func.lower(Usuario.usuario) == nombre_usuario)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese nombre de usuario ya está tomado. Prueba con otro.",
            )
    else:
        nombre_usuario = None

    usuario = Usuario(
        email=email,
        usuario=nombre_usuario,
        password_hash=hash_password(datos.password),
        nombre=datos.representante,
        rol=RolUsuario.AFILIADO,
    )
    db.add(usuario)
    db.flush()

    afiliado = Afiliado(
        usuario_id=usuario.id,
        rnc_cedula=datos.rnc_cedula.strip(),
        nombre=datos.nombre_empresa.strip(),
        categoria=datos.categoria,
        # Queda pendiente hasta que el staff valide RNC, cédula y soporte de pago.
        estado=EstadoAfiliado.PENDIENTE,
        representante=datos.representante,
        email=email,
        telefono=datos.telefono,
        direccion=datos.direccion,
        fecha_afiliacion=date.today(),
        cuota_anual=settings.CUOTA_ANUAL_DEFAULT,
    )
    db.add(afiliado)
    db.commit()
    db.refresh(usuario)
    return _emitir(db, usuario)


@router.post("/refresh", response_model=TokenPair)
def refrescar(datos: RefreshRequest, db: DbSession) -> TokenPair:
    payload = decodificar_token(datos.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión expirada."
        )
    usuario = db.get(Usuario, payload["sub"])
    if usuario is None or not usuario.activo:
        raise CREDENCIALES
    return _emitir(db, usuario)


@router.get("/me", response_model=UsuarioOut)
def yo(usuario: UsuarioActual) -> UsuarioOut:
    return UsuarioOut.model_validate(usuario)


@router.post("/cambiar-password", response_model=Mensaje)
def cambiar_password(
    datos: CambiarPassword, usuario: UsuarioActual, db: DbSession
) -> Mensaje:
    if not verificar_password(datos.password_actual, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="La contraseña actual no coincide."
        )
    usuario.password_hash = hash_password(datos.password_nueva)
    db.commit()
    return Mensaje(detail="Contraseña actualizada.")
