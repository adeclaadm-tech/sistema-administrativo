"""Envío de recordatorios de vencimiento."""

import uuid
from datetime import date
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import AreaContacto


class DestinoRecordatorio(str, Enum):
    """A quién se le manda.

    Por defecto contabilidad, que es quien paga. El staff puede desviarlo al
    comercial o al correo general de la empresa cuando el contable no
    responde.
    """

    AUTOMATICO = "automatico"
    CONTABILIDAD = "contabilidad"
    COMERCIAL = "comercial"
    MARKETING = "marketing"
    EMPRESA = "empresa"
    OTRO = "otro"


class RecordatorioRequest(BaseModel):
    destino: DestinoRecordatorio = DestinoRecordatorio.AUTOMATICO
    # Solo con destino "otro": una dirección suelta, para casos puntuales.
    email: EmailStr | None = None
    # Texto que el staff agrega al cuerpo del correo. Va tal cual, así que
    # sirve para acuerdos particulares: "quedamos en que pagan en dos partes".
    nota: str | None = Field(None, max_length=600)
    adjuntar_proforma: bool = True


class CandidatoRecordatorio(BaseModel):
    """Una fila del preview: a quién le tocaría el aviso y por qué."""

    afiliado_id: uuid.UUID
    afiliado_nombre: str
    email: str | None = None
    fecha_vencimiento: date | None = None
    dias: int | None = None
    motivo: str
    proforma: str | None = None


class ResumenEnvio(BaseModel):
    enviados: int = 0
    sin_correo: int = 0
    fallidos: int = 0
    detalle: list[str] = []


class DestinatarioPosible(BaseModel):
    destino: DestinoRecordatorio
    etiqueta: str
    email: str | None = None
    area: AreaContacto | None = None
