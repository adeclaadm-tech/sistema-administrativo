import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import EstadoDocumento, TipoDocumento
from app.schemas.common import ORMModel


class DocumentoOut(ORMModel):
    id: uuid.UUID
    afiliado_id: uuid.UUID
    tipo: TipoDocumento
    estado: EstadoDocumento
    nombre_archivo: str | None = None
    content_type: str | None = None
    tamano_bytes: int | None = None
    fecha_subida: datetime
    fecha_revision: datetime | None = None
    motivo_rechazo: str | None = None
    # Enlace listo para abrir: público si el bucket lo es, firmado si no.
    url: str | None = None


class DocumentoEnCola(BaseModel):
    """Fila de la cola de revisión del dashboard admin (pantalla 1f)."""

    id: uuid.UUID
    afiliado_id: uuid.UUID
    afiliado_nombre: str
    tipo: TipoDocumento
    nombre_archivo: str | None = None
    fecha_subida: datetime
    dias_en_espera: int


class RevisionDocumento(BaseModel):
    """Aprobar o rechazar. El rechazo exige motivo: el afiliado tiene que
    saber qué corregir antes de volver a subir."""

    aprobado: bool
    motivo_rechazo: str | None = Field(None, max_length=500)

    def validar(self) -> None:
        if not self.aprobado and not (self.motivo_rechazo or "").strip():
            raise ValueError("Un rechazo necesita motivo.")


class DocumentoSubidoOut(BaseModel):
    documento: DocumentoOut
    mensaje: str = "Documento recibido. El equipo lo revisa en 3 días laborables."
