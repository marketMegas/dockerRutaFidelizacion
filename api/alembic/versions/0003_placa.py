"""Placa del vehiculo en el cliente

Revision ID: 0003_placa
Revises: 0002_cedula
Create Date: 2026-10-16

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_placa"
down_revision: str | None = "0002_cedula"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clientes", sa.Column("placa", sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column("clientes", "placa")
