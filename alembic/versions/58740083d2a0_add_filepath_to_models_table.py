"""add filepath to models table

Revision ID: 58740083d2a0
Revises: f5d1e6c7e8b3
Create Date: 2025-07-21 14:07:14.416649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58740083d2a0'
down_revision: Union[str, None] = 'f5d1e6c7e8b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
