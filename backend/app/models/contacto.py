import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import AreaContacto

if TYPE_CHECKING:
    from app.models.afiliado import Afiliado


class ContactoAfiliado(Base, UUIDMixin, TimestampMixin):
    """Persona de contacto de la empresa afiliada, por área.

    Cada afiliado registra un contacto por área (contabilidad, marketing,
    comercial) con nombre, cargo, teléfono y correo. Va en tabla aparte y no
    como doce columnas dentro de `afiliados`: así se agrega un área nueva sin
    migrar la ficha completa, y se consulta "todos los contactos de
    contabilidad" con un solo filtro.
    """

    __tablename__ = "contactos_afiliado"
    __table_args__ = (
        UniqueConstraint("afiliado_id", "area", name="uq_contacto_afiliado_area"),
    )

    afiliado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("afiliados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    area: Mapped[AreaContacto] = mapped_column(
        SAEnum(AreaContacto, name="area_contacto", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )

    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    cargo: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    afiliado: Mapped["Afiliado"] = relationship(back_populates="contactos")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ContactoAfiliado {self.area.value} · {self.nombre}>"
