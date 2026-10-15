"""Esquema inicial: clientes, ventas, ledger, reglas, recompensas, canjes

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-15

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telefono", sa.String(length=20), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("puntos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("otp_hash", sa.String(length=128), nullable=True),
        sa.Column("otp_expires_at", sa.DateTime(), nullable=True),
        sa.Column("otp_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_clientes_telefono", "clientes", ["telefono"], unique=True)

    op.create_table(
        "reglas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=80), nullable=False, unique=True),
        sa.Column("puntos_por_litro", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("prioridad", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("desde", sa.DateTime(), nullable=True),
        sa.Column("hasta", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "recompensas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("costo_puntos", sa.Integer(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "ventas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("volumen_litros", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("monto", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("puntos_otorgados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("placa", sa.String(length=10), nullable=True),
        sa.Column("estacion_id", sa.String(length=40), nullable=True),
        sa.Column("origen", sa.String(length=20), nullable=False, server_default="simulador"),
        sa.Column("regla_id", sa.Integer(), sa.ForeignKey("reglas.id"), nullable=True),
        sa.Column("id_externo", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ventas_cliente_id", "ventas", ["cliente_id"])
    op.create_index("ix_ventas_id_externo", "ventas", ["id_externo"], unique=True)
    op.create_index("ix_ventas_created_at", "ventas", ["created_at"])

    op.create_table(
        "ledger_puntos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("saldo_resultante", sa.Integer(), nullable=False),
        sa.Column("referencia", sa.String(length=80), nullable=True),
        sa.Column("motivo", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ledger_puntos_cliente_id", "ledger_puntos", ["cliente_id"])
    op.create_index("ix_ledger_puntos_created_at", "ledger_puntos", ["created_at"])

    op.create_table(
        "canjes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("recompensa_id", sa.Integer(), sa.ForeignKey("recompensas.id"), nullable=False),
        sa.Column("puntos_costo", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="pendiente"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_canjes_cliente_id", "canjes", ["cliente_id"])


def downgrade() -> None:
    op.drop_table("canjes")
    op.drop_table("ledger_puntos")
    op.drop_table("ventas")
    op.drop_table("recompensas")
    op.drop_table("reglas")
    op.drop_table("clientes")
