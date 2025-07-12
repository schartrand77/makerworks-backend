"""add avatar url fields

Revision ID: ae4abeae4727
Revises: 15cd32aee1ed
Create Date: 2025-07-09 23:32:43.652129

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ae4abeae4727"
down_revision: str | None = "15cd32aee1ed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("avatar_url", sa.String(), nullable=True))
    op.add_column("users", sa.Column("avatar_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "avatar_updated_at")
    op.drop_column("users", "avatar_url")
