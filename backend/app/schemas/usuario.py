import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.enums import RolUsuario, SubRolAdmin
from app.schemas.common import ORMModel


class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=2, max_length=160)


class UsuarioStaffCrear(UsuarioBase):
    """Alta de una cuenta del panel. Solo la hace un administrador."""

    password: str = Field(min_length=8, max_length=128)
    sub_rol: SubRolAdmin = SubRolAdmin.CONSULTOR


class UsuarioActualizar(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=160)
    email: EmailStr | None = None
    sub_rol: SubRolAdmin | None = None
    activo: bool | None = None


class MiCuentaActualizar(BaseModel):
    """Lo que el propio usuario puede cambiar de su cuenta."""

    nombre: str | None = Field(None, min_length=2, max_length=160)
    usuario: str | None = Field(
        None, min_length=3, max_length=60, pattern=r"^[a-zA-Z0-9._-]+$"
    )


class CambiarPassword(BaseModel):
    password_actual: str
    password_nueva: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def distinta(self):
        if self.password_actual == self.password_nueva:
            raise ValueError("La contraseña nueva tiene que ser distinta de la actual.")
        return self


class UsuarioOut(ORMModel):
    id: uuid.UUID
    email: EmailStr
    usuario: str | None = None
    nombre: str
    rol: RolUsuario
    sub_rol: SubRolAdmin | None = None
    activo: bool
    creado_en: datetime
