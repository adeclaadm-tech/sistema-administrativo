"""Nombre de usuario para entrar, y período en la proforma.

El nombre de usuario es una alternativa al correo en el login: varios
representantes no recuerdan con qué dirección los dieron de alta.

El período de la proforma existe para poder detectar que ya se emitió un
cobro para ese año: sin él, pulsar "Emitir proforma" dos veces creaba dos
documentos válidos para la misma cuota.

Revision ID: 0003_usuario_y_periodo
Revises: 0002_categorias_reales
Create Date: 2026-09-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_usuario_y_periodo"
down_revision: Union[str, None] = "0002_categorias_reales"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("usuario", sa.String(60), nullable=True))
    op.create_index("ix_usuarios_usuario", "usuarios", ["usuario"], unique=True)

    op.add_column("proformas", sa.Column("periodo", sa.Integer(), nullable=True))
    op.create_index("ix_proformas_periodo", "proformas", ["periodo"])

    # Las proformas que ya existen llevan el año en la fecha de emisión, que es
    # de dónde salía el período antes de tener columna propia.
    op.execute(
        "UPDATE proformas SET periodo = EXTRACT(year FROM fecha_generacion)::int "
        "WHERE periodo IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_proformas_periodo", table_name="proformas")
    op.drop_column("proformas", "periodo")
    op.drop_index("ix_usuarios_usuario", table_name="usuarios")
    op.drop_column("usuarios", "usuario")
