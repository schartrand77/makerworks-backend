"""add glb_path to model_metadata

Revision ID: 18a82e28fe74
Revises: 58740083d2a0
Create Date: 2025-07-21 17:45:33.645425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18a82e28fe74'
down_revision: Union[str, None] = '58740083d2a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
