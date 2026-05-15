"""tablas iniciales

Revision ID: e08aa9419c71
Revises: 
Create Date: ...

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'e08aa9419c71'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('farmacias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cadena', sa.String(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=True),
        sa.Column('direccion', sa.String(), nullable=True),
        sa.Column('comuna', sa.String(), nullable=True),
        sa.Column('ubicacion', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, from_text='ST_GeogFromText', name='geography'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_farmacias_comuna', 'farmacias', ['comuna'], unique=False)

    op.create_table('principios_activos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('dosis', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_principios_activos_nombre', 'principios_activos', ['nombre'], unique=False)

    op.create_table('medicamentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre_comercial', sa.String(), nullable=False),
        sa.Column('laboratorio', sa.String(), nullable=True),
        sa.Column('es_bioequivalente', sa.Boolean(), nullable=True),
        sa.Column('principio_activo_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['principio_activo_id'], ['principios_activos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_medicamentos_nombre_comercial', 'medicamentos', ['nombre_comercial'], unique=False)

    op.create_table('precios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('medicamento_id', sa.Integer(), nullable=True),
        sa.Column('farmacia_id', sa.Integer(), nullable=True),
        sa.Column('precio', sa.Float(), nullable=False),
        sa.Column('stock', sa.Boolean(), nullable=True),
        sa.Column('fecha_scrape', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['farmacia_id'], ['farmacias.id'], ),
        sa.ForeignKeyConstraint(['medicamento_id'], ['medicamentos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_precios_fecha_scrape', 'precios', ['fecha_scrape'], unique=False)
    op.create_index('ix_precios_medicamento_id', 'precios', ['medicamento_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_precios_medicamento_id', table_name='precios')
    op.drop_index('ix_precios_fecha_scrape', table_name='precios')
    op.drop_table('precios')
    op.drop_index('ix_medicamentos_nombre_comercial', table_name='medicamentos')
    op.drop_table('medicamentos')
    op.drop_index('ix_principios_activos_nombre', table_name='principios_activos')
    op.drop_table('principios_activos')
    op.drop_index('ix_farmacias_comuna', table_name='farmacias')
    op.drop_table('farmacias')