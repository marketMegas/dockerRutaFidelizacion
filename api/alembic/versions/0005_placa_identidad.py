"""Placa como identidad de acceso

Revision ID: 0005_placa_identidad
Revises: 0004_imagen
Create Date: 2026-10-19

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_placa_identidad"
down_revision: str | None = "0004_imagen"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            "UPDATE clientes SET placa = regexp_replace(upper(trim(placa)), '[^A-Z0-9]', '', 'g') "
            "WHERE placa IS NOT NULL"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE clientes SET placa = substr('PLACA', 1, 10 - length(id::text)) || id "
            "WHERE placa IS NULL OR placa = ''"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE clientes c SET placa = substr(c.placa, 1, 10 - length(c.id::text) - 1) || '-' || c.id "
            "FROM (SELECT id, row_number() OVER (PARTITION BY placa ORDER BY id) AS rn FROM clientes) d "
            "WHERE d.id = c.id AND d.rn > 1"
        )
    )

    op.alter_column("clientes", "placa", existing_type=sa.String(length=10), nullable=False)
    op.create_index("ix_clientes_placa", "clientes", ["placa"], unique=True)
    op.alter_column("clientes", "cedula", existing_type=sa.String(length=15), nullable=True)


def downgrade() -> None:
    op.drop_index("ix_clientes_placa", table_name="clientes")
    op.alter_column("clientes", "cedula", existing_type=sa.String(length=15), nullable=False)
    op.alter_column("clientes", "placa", existing_type=sa.String(length=10), nullable=True)
