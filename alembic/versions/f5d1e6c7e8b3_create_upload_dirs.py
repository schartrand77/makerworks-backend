"""create upload directories for users

Revision ID: f5d1e6c7e8b3
Revises: b6f0f66d0991
Create Date: 2025-07-21

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from uuid import UUID
from pathlib import Path

# revision identifiers, used by Alembic.
revision = 'f5d1e6c7e8b3'
down_revision = 'b6f0f66d0991'
branch_labels = None
depends_on = None


def create_upload_dir(user_id: UUID):
    """
    Create /uploads/users/<user_id>/avatars/ and place default avatar if desired.
    """
    base_dir = Path('uploads/users') / str(user_id) / 'avatars'
    base_dir.mkdir(parents=True, exist_ok=True)

    default_avatar = Path('static/default-avatar.jpg')
    target = base_dir / 'avatar.jpg'
    if default_avatar.exists() and not target.exists():
        target.write_bytes(default_avatar.read_bytes())


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    users_table = sa.table(
        'users',
        sa.column('id', sa.String),
    )

    results = session.execute(sa.select(users_table.c.id)).scalars().all()
    for user_id in results:
        create_upload_dir(user_id)

    session.commit()


def downgrade():
    # no-op: don’t delete user folders
    pass
