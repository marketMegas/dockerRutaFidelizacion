"""Cuentas de isleros y auditoria de registros de clientes

Revision ID: 0008_isleros
Revises: 0007_catalogo_niveles
Create Date: 2026-10-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_isleros"
down_revision: str | None = "0007_catalogo_niveles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario", sa.String(length=60), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False, server_default="islero"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ultimo_acceso", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_usuarios_usuario", "usuarios", ["usuario"], unique=True)

    op.create_table(
        "auditoria_clientes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("placa", sa.String(length=10), nullable=False),
        sa.Column("accion", sa.String(length=20), nullable=False),
        sa.Column("detalle", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_auditoria_clientes_usuario_id", "auditoria_clientes", ["usuario_id"])
    op.create_index("ix_auditoria_clientes_cliente_id", "auditoria_clientes", ["cliente_id"])
    op.create_index("ix_auditoria_clientes_created_at", "auditoria_clientes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_auditoria_clientes_created_at", table_name="auditoria_clientes")
    op.drop_index("ix_auditoria_clientes_cliente_id", table_name="auditoria_clientes")
    op.drop_index("ix_auditoria_clientes_usuario_id", table_name="auditoria_clientes")
    op.drop_table("auditoria_clientes")
    op.drop_index("ix_usuarios_usuario", table_name="usuarios")
    op.drop_table("usuarios")
