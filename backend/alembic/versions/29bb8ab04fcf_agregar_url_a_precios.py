"""agregar url a precios

Revision ID: 29bb8ab04fcf
Revises: e08aa9419c71
Create Date: 2026-05-16 05:08:31.917715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29bb8ab04fcf'
down_revision: Union[str, Sequence[str], None] = 'e08aa9419c71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("precios", sa.Column("url", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("precios", "url")
