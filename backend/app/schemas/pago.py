import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import MetodoPago
from app.schemas.common import ORMModel


class PagoCrear(BaseModel):
    """Registro de pago desde el panel (modal de la pantalla 1h)."""

    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    fecha: date
    metodo: MetodoPago = MetodoPago.TRANSFERENCIA
    referencia: str | None = Field(None, max_length=120)
    concepto: str | None = Field(None, max_length=200)
    periodo: int | None = Field(None, ge=2000, le=2100)
    comprobante_url: str | None = None
    notas: str | None = None
    moneda: str = Field("DOP", min_length=3, max_length=3)
    # Proforma que este pago liquida. Es el caso normal: la proforma se emitió
    # antes para que el afiliado supiera cuánto y a dónde pagar.
    proforma_id: uuid.UUID | None = None
    # Solo para cobros que entraron sin proforma previa (efectivo en
    # ventanilla, por ejemplo): la emite después, ya saldada.
    generar_proforma: bool = False
    # Empuja el vencimiento del afiliado un año hacia adelante y lo activa.
    renovar_afiliacion: bool = False


class PagoActualizar(BaseModel):
    monto: Decimal | None = Field(None, gt=0, max_digits=12, decimal_places=2)
    fecha: date | None = None
    metodo: MetodoPago | None = None
    referencia: str | None = Field(None, max_length=120)
    concepto: str | None = Field(None, max_length=200)
    periodo: int | None = Field(None, ge=2000, le=2100)
    comprobante_url: str | None = None
    notas: str | None = None


class PagoOut(ORMModel):
    id: uuid.UUID
    afiliado_id: uuid.UUID
    monto: Decimal
    moneda: str
    fecha: date
    metodo: MetodoPago
    referencia: str | None = None
    concepto: str | None = None
    periodo: int | None = None
    comprobante_url: str | None = None
    notas: str | None = None
    registrado_por_usuario_id: uuid.UUID | None = None
    creado_en: datetime


class PagoConProformaOut(BaseModel):
    pago: PagoOut
    proforma_numero: str | None = None
    proforma_id: uuid.UUID | None = None
