"""Categorías reales del padrón y RNC opcional.

Las clases A/B/C eran un invento del andamiaje inicial. El padrón que maneja
ADECLA clasifica por tipo de afiliación —constructor, proveedor,
desarrollador— igual que el sistema de inscripciones al torneo, y hay
empresas sin tipo asignado.

El RNC pasa a ser opcional por el mismo motivo: el listado real no lo trae
para todas, y rellenarlo con valores inventados ensucia el dato.

Revision ID: 0002_categorias_reales
Revises: 0001_esquema_inicial
Create Date: 2026-09-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_categorias_reales"
down_revision: Union[str, None] = "0001_esquema_inicial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NUEVOS = ("constructor", "proveedor", "desarrollador")
VIEJOS = ("clase_a", "clase_b", "clase_c")


def upgrade() -> None:
    # Postgres no deja alterar los valores de un ENUM en uso, así que se pasa
    # la columna a texto, se reconstruye el tipo y se vuelve a convertir.
    # El orden importa: hay que soltar el NOT NULL antes de vaciar los
    # valores, o el UPDATE choca contra la restricción que todavía está viva.
    op.execute("ALTER TABLE afiliados ALTER COLUMN categoria DROP DEFAULT")
    op.execute("ALTER TABLE afiliados ALTER COLUMN categoria DROP NOT NULL")
    op.execute("ALTER TABLE afiliados ALTER COLUMN categoria TYPE text USING categoria::text")

    # Las clases viejas no significaban nada real: se descartan en vez de
    # traducirlas a un tipo que nadie asignó.
    op.execute("UPDATE afiliados SET categoria = NULL WHERE categoria IN ('clase_a','clase_b','clase_c')")

    op.execute("DROP TYPE categoria_afiliado")
    op.execute("CREATE TYPE categoria_afiliado AS ENUM ('constructor','proveedor','desarrollador')")
    op.execute(
        "ALTER TABLE afiliados ALTER COLUMN categoria TYPE categoria_afiliado "
        "USING categoria::categoria_afiliado"
    )

    op.alter_column("afiliados", "rnc_cedula", existing_type=sa.String(32), nullable=True)


def downgrade() -> None:
    op.execute("ALTER TABLE afiliados ALTER COLUMN categoria TYPE text USING categoria::text")
    op.execute(
        "UPDATE afiliados SET categoria = NULL "
        "WHERE categoria IN ('constructor','proveedor','desarrollador')"
    )
    op.execute("DROP TYPE categoria_afiliado")
    op.execute("CREATE TYPE categoria_afiliado AS ENUM ('clase_a','clase_b','clase_c')")
    op.execute(
        "ALTER TABLE afiliados ALTER COLUMN categoria TYPE categoria_afiliado "
        "USING categoria::categoria_afiliado"
    )
    op.execute("UPDATE afiliados SET categoria = 'clase_b' WHERE categoria IS NULL")
    op.alter_column(
        "afiliados",
        "categoria",
        existing_type=sa.Enum(*VIEJOS, name="categoria_afiliado"),
        nullable=False,
    )

    # Volver a exigir el RNC necesita un valor en las filas que no lo tienen.
    op.execute(
        "UPDATE afiliados SET rnc_cedula = 'SIN-RNC-' || left(id::text, 8) WHERE rnc_cedula IS NULL"
    )
    op.alter_column("afiliados", "rnc_cedula", existing_type=sa.String(32), nullable=False)
