"""Cedula como identidad de acceso de clientes

Revision ID: 0002_cedula
Revises: 0001_initial
Create Date: 2026-10-16

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_cedula"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clientes", sa.Column("cedula", sa.String(length=15), nullable=False))
    op.create_index("ix_clientes_cedula", "clientes", ["cedula"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_clientes_cedula", table_name="clientes")
    op.drop_column("clientes", "cedula")
