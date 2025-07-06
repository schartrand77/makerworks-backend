"""add filament fields

Revision ID: 78984906fa0a
Revises: aec0165d1a63
Create Date: 2025-07-06 14:49:22.755888

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "78984906fa0a"
down_revision: str | None = "aec0165d1a63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename existing columns
    op.alter_column("filaments", "group", new_column_name="type")
    op.alter_column("filaments", "color_hex", new_column_name="color")

    # Add new columns
    op.add_column("filaments", sa.Column("subtype", sa.String(), nullable=True))
    op.add_column("filaments", sa.Column("surface", sa.String(), nullable=True))
    op.add_column("filaments", sa.Column("texture", sa.String(), nullable=True))
    op.add_column("filaments", sa.Column("color_name", sa.String(), nullable=True))
    op.add_column(
        "filaments",
        sa.Column("currency", sa.String(), server_default="USD", nullable=True),
    )
    op.add_column(
        "filaments", sa.Column("is_biodegradable", sa.Boolean(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove added columns
    op.drop_column("filaments", "is_biodegradable")
    op.drop_column("filaments", "currency")
    op.drop_column("filaments", "color_name")
    op.drop_column("filaments", "texture")
    op.drop_column("filaments", "surface")
    op.drop_column("filaments", "subtype")

    # Rename columns back to original names
    op.alter_column("filaments", "color", new_column_name="color_hex")
    op.alter_column("filaments", "type", new_column_name="group")
