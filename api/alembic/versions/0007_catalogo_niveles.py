"""Catalogo en archivo y niveles por consumo: los premios son codigos

El catalogo de premios deja de vivir en la base de datos (tabla `recompensas`)
y pasa a un archivo JSON que edita el panel. Cada canje guarda el codigo
entregado al cliente y una copia del nombre del premio.

Revision ID: 0007_catalogo_niveles
Revises: 0006_vehiculos
Create Date: 2026-10-22

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_catalogo_niveles"
down_revision: str | None = "0006_vehiculos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Se recrea `canjes`: la tabla vieja tiene FK a `recompensas` y el estado
    # de entrega, que ya no aplican. Es la via portable de soltar la FK.
    op.drop_table("canjes")
    op.create_table(
        "canjes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("premio_clave", sa.String(length=60), nullable=False),
        sa.Column("premio_nombre", sa.String(length=120), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("puntos_costo", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_canjes_cliente_id", "canjes", ["cliente_id"])
    op.create_index("ix_canjes_codigo", "canjes", ["codigo"], unique=True)

    op.drop_table("recompensas")


def downgrade() -> None:
    op.create_table(
        "recompensas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("imagen", sa.String(length=500), nullable=True),
        sa.Column("costo_puntos", sa.Integer(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.drop_index("ix_canjes_codigo", table_name="canjes")
    op.drop_index("ix_canjes_cliente_id", table_name="canjes")
    op.drop_table("canjes")
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
