import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.afiliado import Afiliado
    from app.models.pago import Pago


class Proforma(Base, UUIDMixin, TimestampMixin):
    """Comprobante numerado que el afiliado descarga (PRF-2026-0184).

    El número es único y consecutivo por año; se genera en
    `app.services.proformas`, nunca lo escribe el cliente.
    """

    __tablename__ = "proformas"

    afiliado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("afiliados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pago_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pagos.id", ondelete="SET NULL"), unique=True, nullable=True
    )

    numero: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    fecha_generacion: Mapped[date] = mapped_column(Date, nullable=False)
    monto: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    concepto: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    afiliado: Mapped["Afiliado"] = relationship(back_populates="proformas")
    pago: Mapped[Optional["Pago"]] = relationship(back_populates="proforma")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Proforma {self.numero}>"
