from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import RolUsuario, SubRolAdmin

if TYPE_CHECKING:
    from app.models.afiliado import Afiliado


class Usuario(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "usuarios"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)

    rol: Mapped[RolUsuario] = mapped_column(
        SAEnum(RolUsuario, name="rol_usuario", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=RolUsuario.AFILIADO,
    )
    # Solo se llena cuando rol == admin.
    sub_rol: Mapped[Optional[SubRolAdmin]] = mapped_column(
        SAEnum(SubRolAdmin, name="sub_rol_admin", values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    afiliado: Mapped[Optional["Afiliado"]] = relationship(
        back_populates="usuario", uselist=False
    )

    @property
    def es_admin(self) -> bool:
        return self.rol == RolUsuario.ADMIN

    @property
    def puede_escribir(self) -> bool:
        """El consultor mira; el administrador decide."""
        return self.rol == RolUsuario.ADMIN and self.sub_rol == SubRolAdmin.ADMINISTRADOR

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Usuario {self.email} ({self.rol.value})>"
