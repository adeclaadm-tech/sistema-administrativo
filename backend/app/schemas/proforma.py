import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ProformaCrear(BaseModel):
    afiliado_id: uuid.UUID
    pago_id: uuid.UUID | None = None
    # Año que cubre el cobro. Por defecto el de la fecha de emisión.
    periodo: int | None = Field(None, ge=2000, le=2100)
    monto: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    concepto: str | None = Field(None, max_length=200)
    fecha_generacion: date | None = None


class ProformaOut(ORMModel):
    id: uuid.UUID
    afiliado_id: uuid.UUID
    afiliado_nombre: str | None = None
    pago_id: uuid.UUID | None = None
    numero: str
    fecha_generacion: date
    periodo: int | None = None
    monto: Decimal | None = None
    concepto: str | None = None
    pdf_url: str | None = None
    url: str | None = None
