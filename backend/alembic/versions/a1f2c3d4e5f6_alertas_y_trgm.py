"""alertas de precio + indices trigram para busqueda

Revision ID: a1f2c3d4e5f6
Revises: 29bb8ab04fcf
Create Date: 2026-06-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1f2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "29bb8ab04fcf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Indices trigram para que LIKE '%q%' use indice en vez de scan completo.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_med_nombre_trgm "
        "ON medicamentos USING gin (lower(nombre_comercial) gin_trgm_ops);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_principio_nombre_trgm "
        "ON principios_activos USING gin (lower(nombre) gin_trgm_ops);"
    )

    # Tabla de alertas de precio.
    op.create_table(
        "alertas_precio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("medicamento_id", sa.Integer(), nullable=True),
        sa.Column("precio_objetivo", sa.Float(), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=True),
        sa.Column("creada", sa.DateTime(), nullable=True),
        sa.Column("ultima_notificacion", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["medicamento_id"], ["medicamentos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alertas_precio_email", "alertas_precio", ["email"])
    op.create_index("ix_alertas_precio_activa", "alertas_precio", ["activa"])
    op.create_index(
        "ix_alertas_precio_medicamento_id", "alertas_precio", ["medicamento_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_alertas_precio_medicamento_id", table_name="alertas_precio")
    op.drop_index("ix_alertas_precio_activa", table_name="alertas_precio")
    op.drop_index("ix_alertas_precio_email", table_name="alertas_precio")
    op.drop_table("alertas_precio")
    op.execute("DROP INDEX IF EXISTS ix_principio_nombre_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_med_nombre_trgm;")
