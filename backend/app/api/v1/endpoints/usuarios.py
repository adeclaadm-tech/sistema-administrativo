"""Usuarios del staff. Alta, edición y baja las hace un administrador."""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.core.deps import Administrador, DbSession
from app.core.security import hash_password
from app.models.enums import RolUsuario
from app.models.usuario import Usuario
from app.schemas.common import Mensaje
from app.schemas.usuario import UsuarioActualizar, UsuarioOut, UsuarioStaffCrear

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut], summary="Listar cuentas del panel")
def listar(_: Administrador, db: DbSession) -> list[UsuarioOut]:
    filas = db.scalars(
        select(Usuario).where(Usuario.rol == RolUsuario.ADMIN).order_by(Usuario.nombre)
    ).all()
    return [UsuarioOut.model_validate(u) for u in filas]


@router.post(
    "", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED, summary="Crear cuenta de staff"
)
def crear(datos: UsuarioStaffCrear, admin: Administrador, db: DbSession) -> UsuarioOut:
    email = datos.email.lower()
    if db.scalar(select(Usuario).where(func.lower(Usuario.email) == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ya existe una cuenta con este correo."
        )
    usuario = Usuario(
        email=email,
        password_hash=hash_password(datos.password),
        nombre=datos.nombre,
        rol=RolUsuario.ADMIN,
        sub_rol=datos.sub_rol,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return UsuarioOut.model_validate(usuario)


@router.patch("/{usuario_id}", response_model=UsuarioOut, summary="Editar cuenta de staff")
def actualizar(
    usuario_id: uuid.UUID, datos: UsuarioActualizar, admin: Administrador, db: DbSession
) -> UsuarioOut:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or usuario.rol != RolUsuario.ADMIN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada.")
    if usuario.id == admin.id and datos.activo is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes desactivar tu propia cuenta."
        )
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, str(valor) if campo == "email" and valor else valor)
    db.commit()
    db.refresh(usuario)
    return UsuarioOut.model_validate(usuario)


@router.delete("/{usuario_id}", response_model=Mensaje, summary="Desactivar cuenta de staff")
def desactivar(usuario_id: uuid.UUID, admin: Administrador, db: DbSession) -> Mensaje:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or usuario.rol != RolUsuario.ADMIN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada.")
    if usuario.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes desactivar tu propia cuenta."
        )
    # Baja lógica: los pagos y revisiones guardan quién los hizo.
    usuario.activo = False
    db.commit()
    return Mensaje(detail="Cuenta desactivada.")
