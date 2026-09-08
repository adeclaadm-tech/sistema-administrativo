import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import EstadoDocumento, TipoDocumento

if TYPE_CHECKING:
    from app.models.afiliado import Afiliado
    from app.models.usuario import Usuario


class Documento(Base, UUIDMixin, TimestampMixin):
    """Archivo cargado por el afiliado y revisado por el staff.

    `archivo_url` guarda la llave del objeto en el bucket, no una ruta del
    disco del servidor: el contenedor es efímero y el archivo tiene que
    sobrevivir a un redeploy.
    """

    __tablename__ = "documentos"

    afiliado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("afiliados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoDocumento] = mapped_column(
        SAEnum(TipoDocumento, name="tipo_documento", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    estado: Mapped[EstadoDocumento] = mapped_column(
        SAEnum(
            EstadoDocumento,
            name="estado_documento",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=EstadoDocumento.PENDIENTE,
        index=True,
    )

    archivo_url: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_archivo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    tamano_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    fecha_subida: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    fecha_revision: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revisado_por_usuario_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    motivo_rechazo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    afiliado: Mapped["Afiliado"] = relationship(back_populates="documentos")
    revisado_por: Mapped[Optional["Usuario"]] = relationship(
        foreign_keys=[revisado_por_usuario_id]
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Documento {self.tipo.value} · {self.estado.value}>"
