import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import CategoriaAfiliado
from app.schemas.usuario import UsuarioOut


class LoginRequest(BaseModel):
    """Login por JSON.

    El portal de afiliados deja entrar con RNC o con correo, así que el campo
    se llama `identificador` y no `email`. La ruta OAuth2 estándar
    (`/auth/token`, form-urlencoded) sigue existiendo para Swagger.
    """

    identificador: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UsuarioOut
    afiliado_id: uuid.UUID | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class RegistroAfiliadoRequest(BaseModel):
    """Auto-registro del constructor.

    Crea el usuario y su ficha de afiliado en estado `pendiente`: el staff
    valida los documentos antes de que la afiliación quede vigente. Las
    cuentas del panel no salen de aquí, se crean desde `/usuarios`.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre_empresa: str = Field(min_length=2, max_length=200)
    rnc_cedula: str = Field(min_length=5, max_length=32)
    representante: str = Field(min_length=2, max_length=160)
    telefono: str | None = Field(None, max_length=40)
    direccion: str | None = None
    categoria: CategoriaAfiliado = CategoriaAfiliado.CLASE_B


class SolicitarResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password_nueva: str = Field(min_length=8, max_length=128)
