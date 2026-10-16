"""Imagen de referencia en la recompensa

Revision ID: 0004_imagen
Revises: 0003_placa
Create Date: 2026-10-16

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_imagen"
down_revision: str | None = "0003_placa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("recompensas", sa.Column("imagen", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("recompensas", "imagen")
