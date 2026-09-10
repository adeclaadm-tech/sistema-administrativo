import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import CategoriaAfiliado, EstadoAfiliado

if TYPE_CHECKING:
    from app.models.contacto import ContactoAfiliado
    from app.models.documento import Documento
    from app.models.pago import Pago
    from app.models.proforma import Proforma
    from app.models.usuario import Usuario


class Afiliado(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "afiliados"

    usuario_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )

    # Identificador fiscal de la empresa y llave de búsqueda del staff.
    # Nulo a propósito: el padrón que mantiene ADECLA no lo tiene para todas
    # las empresas, y obligarlo forzaría a inventar valores de relleno que
    # después nadie sabe distinguir de los reales. Postgres permite varios
    # nulos bajo un índice único.
    rnc_cedula: Mapped[Optional[str]] = mapped_column(
        String(32), unique=True, index=True, nullable=True
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    categoria: Mapped[Optional[CategoriaAfiliado]] = mapped_column(
        SAEnum(
            CategoriaAfiliado,
            name="categoria_afiliado",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )
    estado: Mapped[EstadoAfiliado] = mapped_column(
        SAEnum(
            EstadoAfiliado,
            name="estado_afiliado",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=EstadoAfiliado.PENDIENTE,
        index=True,
    )

    representante: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    fecha_afiliacion: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_vencimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    cuota_anual: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    usuario: Mapped[Optional["Usuario"]] = relationship(back_populates="afiliado")
    contactos: Mapped[list["ContactoAfiliado"]] = relationship(
        back_populates="afiliado", cascade="all, delete-orphan", lazy="selectin"
    )
    documentos: Mapped[list["Documento"]] = relationship(
        back_populates="afiliado", cascade="all, delete-orphan"
    )
    pagos: Mapped[list["Pago"]] = relationship(
        back_populates="afiliado", cascade="all, delete-orphan"
    )
    proformas: Mapped[list["Proforma"]] = relationship(
        back_populates="afiliado", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Afiliado {self.rnc_cedula} · {self.nombre}>"
