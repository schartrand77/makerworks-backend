"""add uploader_id to models table

Revision ID: a56dc382ec63
Revises: 9b155f49ab09
Create Date: 2025-07-26 18:15:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a56dc382ec63'
down_revision: Union[str, None] = '9b155f49ab09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'models',
        sa.Column('uploader_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'models_uploader_id_fkey',
        'models', 'users',
        ['uploader_id'], ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('models_uploader_id_fkey', 'models', type_='foreignkey')
    op.drop_column('models', 'uploader_id')
