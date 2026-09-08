import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ProformaCrear(BaseModel):
    afiliado_id: uuid.UUID
    pago_id: uuid.UUID | None = None
    monto: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    concepto: str | None = Field(None, max_length=200)
    fecha_generacion: date | None = None


class ProformaOut(ORMModel):
    id: uuid.UUID
    afiliado_id: uuid.UUID
    pago_id: uuid.UUID | None = None
    numero: str
    fecha_generacion: date
    monto: Decimal | None = None
    concepto: str | None = None
    pdf_url: str | None = None
    url: str | None = None
