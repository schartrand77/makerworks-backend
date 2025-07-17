"""add estimate settings and filament pricing tables, extend models

Revision ID: 8f6fe02bda3b
Revises: ed4feb1dceb7
Create Date: 2025-07-17 10:37:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8f6fe02bda3b'
down_revision: Union[str, None] = 'ed4feb1dceb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'filament_pricing',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('filament_id', sa.UUID(), nullable=False),
        sa.Column('price_per_gram', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['filament_id'], ['filaments.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_filament_pricing_id'), 'filament_pricing', ['id'], unique=False)

    op.create_table(
        'estimate_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('custom_text_base_cost', sa.Float(), nullable=True),
        sa.Column('custom_text_cost_per_char', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_estimate_settings_id'), 'estimate_settings', ['id'], unique=False)

    op.add_column('filaments', sa.Column('name', sa.String(), nullable=True))
    op.add_column('filaments', sa.Column('color_name', sa.String(), nullable=True))
    op.add_column('filaments', sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')))
    op.add_column('models', sa.Column('filepath', sa.String(), nullable=True))
    op.add_column('models', sa.Column('file_url', sa.String(), nullable=True))
    op.add_column('models', sa.Column('volume_mm3', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('models', 'volume_mm3')
    op.drop_column('models', 'file_url')
    op.drop_column('models', 'filepath')
    op.drop_column('filaments', 'is_active')
    op.drop_column('filaments', 'color_name')
    op.drop_column('filaments', 'name')
    op.drop_index(op.f('ix_estimate_settings_id'), table_name='estimate_settings')
    op.drop_table('estimate_settings')
    op.drop_index(op.f('ix_filament_pricing_id'), table_name='filament_pricing')
    op.drop_table('filament_pricing')
