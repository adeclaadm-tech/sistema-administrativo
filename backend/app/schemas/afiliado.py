import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import CategoriaAfiliado, EstadoAfiliado
from app.schemas.common import ORMModel
from app.schemas.contacto import ContactoOut, ContactosAfiliado


class AfiliadoBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=200)
    rnc_cedula: str | None = Field(None, min_length=5, max_length=32)
    categoria: CategoriaAfiliado | None = None
    representante: str | None = Field(None, max_length=160)
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=40)
    direccion: str | None = None
    cuota_anual: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    notas: str | None = None


class AfiliadoCrear(AfiliadoBase):
    """Alta desde el panel. El estado por defecto es `pendiente`."""

    estado: EstadoAfiliado = EstadoAfiliado.PENDIENTE
    fecha_afiliacion: date | None = None
    fecha_vencimiento: date | None = None
    contactos: ContactosAfiliado | None = None
    # Si viene, se crea también la cuenta del portal para esta empresa.
    crear_usuario_email: EmailStr | None = None
    crear_usuario_password: str | None = Field(None, min_length=8, max_length=128)


class AfiliadoActualizar(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=200)
    rnc_cedula: str | None = Field(None, min_length=5, max_length=32)
    categoria: CategoriaAfiliado | None = None
    estado: EstadoAfiliado | None = None
    representante: str | None = Field(None, max_length=160)
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=40)
    direccion: str | None = None
    fecha_afiliacion: date | None = None
    fecha_vencimiento: date | None = None
    cuota_anual: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    notas: str | None = None
    contactos: ContactosAfiliado | None = None


class AfiliadoPerfilActualizar(BaseModel):
    """Lo que el propio afiliado puede editar desde su portal.

    Deliberadamente no incluye estado, categoría, RNC ni fechas: eso lo mueve
    el staff.
    """

    representante: str | None = Field(None, max_length=160)
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=40)
    direccion: str | None = None
    contactos: ContactosAfiliado | None = None


class AfiliadoListaOut(ORMModel):
    """Fila de la tabla del panel: solo lo que se ve en pantalla."""

    id: uuid.UUID
    nombre: str
    rnc_cedula: str | None = None
    representante: str | None = None
    categoria: CategoriaAfiliado | None = None
    estado: EstadoAfiliado
    fecha_vencimiento: date | None = None


class AfiliadoOut(ORMModel):
    id: uuid.UUID
    usuario_id: uuid.UUID | None = None
    nombre: str
    rnc_cedula: str | None = None
    categoria: CategoriaAfiliado | None = None
    estado: EstadoAfiliado
    representante: str | None = None
    email: EmailStr | None = None
    telefono: str | None = None
    direccion: str | None = None
    fecha_afiliacion: date | None = None
    fecha_vencimiento: date | None = None
    cuota_anual: Decimal | None = None
    notas: str | None = None
    contactos: list[ContactoOut] = []
    creado_en: datetime
    actualizado_en: datetime


class ResumenAfiliado(BaseModel):
    """Cabecera del dashboard del afiliado (pantalla 1b del mockup)."""

    afiliado: AfiliadoOut
    dias_para_vencer: int | None = None
    progreso_anual: float = Field(0, ge=0, le=1)
    documentos_aprobados: int = 0
    documentos_totales: int = 0
    documentos_pendientes: int = 0
    ultimo_pago: date | None = None
