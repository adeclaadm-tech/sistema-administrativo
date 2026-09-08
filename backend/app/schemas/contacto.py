import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import AreaContacto
from app.schemas.common import ORMModel


class ContactoBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    cargo: str | None = Field(None, max_length=120)
    telefono: str | None = Field(None, max_length=40)
    email: EmailStr | None = None


class ContactoCrear(ContactoBase):
    area: AreaContacto


class ContactoActualizar(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=160)
    cargo: str | None = Field(None, max_length=120)
    telefono: str | None = Field(None, max_length=40)
    email: EmailStr | None = None


class ContactoOut(ORMModel):
    id: uuid.UUID
    afiliado_id: uuid.UUID
    area: AreaContacto
    nombre: str
    cargo: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None


class ContactosAfiliado(BaseModel):
    """Los tres contactos de la ficha, en el orden en que se piden en el formulario."""

    contabilidad: ContactoBase | None = None
    marketing: ContactoBase | None = None
    comercial: ContactoBase | None = None

    def como_lista(self) -> list[ContactoCrear]:
        pares = (
            (AreaContacto.CONTABILIDAD, self.contabilidad),
            (AreaContacto.MARKETING, self.marketing),
            (AreaContacto.COMERCIAL, self.comercial),
        )
        return [
            ContactoCrear(area=area, **datos.model_dump())
            for area, datos in pares
            if datos is not None
        ]
