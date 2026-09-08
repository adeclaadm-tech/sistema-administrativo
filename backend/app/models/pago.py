import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import MetodoPago

if TYPE_CHECKING:
    from app.models.afiliado import Afiliado
    from app.models.proforma import Proforma
    from app.models.usuario import Usuario


class Pago(Base, UUIDMixin, TimestampMixin):
    """Pago registrado por el staff. El afiliado no crea pagos, solo los ve."""

    __tablename__ = "pagos"

    afiliado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("afiliados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    metodo: Mapped[MetodoPago] = mapped_column(
        SAEnum(MetodoPago, name="metodo_pago", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MetodoPago.TRANSFERENCIA,
    )
    referencia: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    concepto: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    # Año de la cuota que cubre el pago; permite agrupar recaudación por período.
    periodo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    comprobante_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    registrado_por_usuario_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    afiliado: Mapped["Afiliado"] = relationship(back_populates="pagos")
    registrado_por: Mapped[Optional["Usuario"]] = relationship(
        foreign_keys=[registrado_por_usuario_id]
    )
    proforma: Mapped[Optional["Proforma"]] = relationship(
        back_populates="pago", uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Pago {self.monto} {self.moneda} · {self.fecha}>"
