"""Esquema inicial: usuarios, afiliados, contactos, documentos, pagos y proformas.

Revision ID: 0001_esquema_inicial
Revises:
Create Date: 2026-09-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_esquema_inicial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


rol_usuario = postgresql.ENUM("afiliado", "admin", name="rol_usuario", create_type=False)
sub_rol_admin = postgresql.ENUM(
    "administrador", "consultor", name="sub_rol_admin", create_type=False
)
categoria_afiliado = postgresql.ENUM(
    "clase_a", "clase_b", "clase_c", name="categoria_afiliado", create_type=False
)
estado_afiliado = postgresql.ENUM(
    "activo", "pendiente", "vencido", name="estado_afiliado", create_type=False
)
area_contacto = postgresql.ENUM(
    "contabilidad", "marketing", "comercial", name="area_contacto", create_type=False
)
tipo_documento = postgresql.ENUM(
    "rnc_nid", "cedula", "soporte_pago", "doc_representante", name="tipo_documento", create_type=False
)
estado_documento = postgresql.ENUM(
    "pendiente", "aprobado", "rechazado", name="estado_documento", create_type=False
)
metodo_pago = postgresql.ENUM(
    "transferencia", "cheque", "efectivo", "tarjeta", "otro", name="metodo_pago", create_type=False
)

TIPOS = (
    rol_usuario,
    sub_rol_admin,
    categoria_afiliado,
    estado_afiliado,
    area_contacto,
    tipo_documento,
    estado_documento,
    metodo_pago,
)


def upgrade() -> None:
    bind = op.get_bind()
    for tipo in TIPOS:
        tipo.create(bind, checkfirst=True)

    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("rol", rol_usuario, nullable=False),
        sa.Column("sub_rol", sub_rol_admin, nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "afiliados",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            unique=True,
            nullable=True,
        ),
        sa.Column("rnc_cedula", sa.String(32), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("categoria", categoria_afiliado, nullable=False),
        sa.Column("estado", estado_afiliado, nullable=False),
        sa.Column("representante", sa.String(160), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("telefono", sa.String(40), nullable=True),
        sa.Column("direccion", sa.Text(), nullable=True),
        sa.Column("fecha_afiliacion", sa.Date(), nullable=True),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=True),
        sa.Column("cuota_anual", sa.Numeric(12, 2), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_afiliados_rnc_cedula", "afiliados", ["rnc_cedula"], unique=True)
    op.create_index("ix_afiliados_nombre", "afiliados", ["nombre"])
    op.create_index("ix_afiliados_estado", "afiliados", ["estado"])
    op.create_index("ix_afiliados_fecha_vencimiento", "afiliados", ["fecha_vencimiento"])

    op.create_table(
        "contactos_afiliado",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "afiliado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("afiliados.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("area", area_contacto, nullable=False),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("cargo", sa.String(120), nullable=True),
        sa.Column("telefono", sa.String(40), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("afiliado_id", "area", name="uq_contacto_afiliado_area"),
    )
    op.create_index("ix_contactos_afiliado_afiliado_id", "contactos_afiliado", ["afiliado_id"])

    op.create_table(
        "documentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "afiliado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("afiliados.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", tipo_documento, nullable=False),
        sa.Column("estado", estado_documento, nullable=False),
        sa.Column("archivo_url", sa.Text(), nullable=False),
        sa.Column("nombre_archivo", sa.String(255), nullable=True),
        sa.Column("content_type", sa.String(120), nullable=True),
        sa.Column("tamano_bytes", sa.BigInteger(), nullable=True),
        sa.Column(
            "fecha_subida", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("fecha_revision", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "revisado_por_usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("motivo_rechazo", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_documentos_afiliado_id", "documentos", ["afiliado_id"])
    op.create_index("ix_documentos_estado", "documentos", ["estado"])

    op.create_table(
        "pagos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "afiliado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("afiliados.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False, server_default="DOP"),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("metodo", metodo_pago, nullable=False),
        sa.Column("referencia", sa.String(120), nullable=True),
        sa.Column("concepto", sa.String(200), nullable=True),
        sa.Column("periodo", sa.Integer(), nullable=True),
        sa.Column("comprobante_url", sa.Text(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column(
            "registrado_por_usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_pagos_afiliado_id", "pagos", ["afiliado_id"])
    op.create_index("ix_pagos_fecha", "pagos", ["fecha"])
    op.create_index("ix_pagos_periodo", "pagos", ["periodo"])

    op.create_table(
        "proformas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "afiliado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("afiliados.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pago_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pagos.id", ondelete="SET NULL"),
            unique=True,
            nullable=True,
        ),
        sa.Column("numero", sa.String(40), nullable=False),
        sa.Column("fecha_generacion", sa.Date(), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=True),
        sa.Column("concepto", sa.String(200), nullable=True),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_proformas_numero", "proformas", ["numero"], unique=True)
    op.create_index("ix_proformas_afiliado_id", "proformas", ["afiliado_id"])


def downgrade() -> None:
    op.drop_table("proformas")
    op.drop_table("pagos")
    op.drop_table("documentos")
    op.drop_table("contactos_afiliado")
    op.drop_table("afiliados")
    op.drop_table("usuarios")

    bind = op.get_bind()
    for tipo in reversed(TIPOS):
        tipo.drop(bind, checkfirst=True)
