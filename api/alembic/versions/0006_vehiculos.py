"""Vehiculos por cliente: un celular puede tener varias placas

Revision ID: 0006_vehiculos
Revises: 0005_placa_identidad
Create Date: 2026-10-19

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_vehiculos"
down_revision: str | None = "0005_placa_identidad"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vehiculos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("placa", sa.String(length=10), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_vehiculos_cliente_id", "vehiculos", ["cliente_id"])
    op.create_index("ix_vehiculos_placa", "vehiculos", ["placa"], unique=True)

    op.add_column("clientes", sa.Column("otp_placa_pendiente", sa.String(length=10), nullable=True))
    op.alter_column("clientes", "placa", existing_type=sa.String(length=10), nullable=True)

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO vehiculos (cliente_id, placa) "
            "SELECT id, placa FROM clientes WHERE placa IS NOT NULL AND placa <> ''"
        )
    )


def downgrade() -> None:
    op.drop_column("clientes", "otp_placa_pendiente")
    op.drop_index("ix_vehiculos_placa", table_name="vehiculos")
    op.drop_index("ix_vehiculos_cliente_id", table_name="vehiculos")
    op.drop_table("vehiculos")
    op.alter_column("clientes", "placa", existing_type=sa.String(length=10), nullable=False)
