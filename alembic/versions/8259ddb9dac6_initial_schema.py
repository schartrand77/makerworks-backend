"""initial schema

Revision ID: 8259ddb9dac6
Revises:
Create Date: 2025-07-20 06:30:45.004870
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8259ddb9dac6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Estimate settings
    op.create_table(
        'estimate_settings',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('custom_text_base_cost', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('custom_text_cost_per_char', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Filaments
    op.create_table(
        'filaments',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('color_name', sa.String(), nullable=False),
        sa.Column('color_hex', sa.String(length=7), nullable=False),
        sa.Column('price_per_kg', sa.Float(), nullable=False),
        sa.Column('surface_texture', sa.String(), nullable=True),
        sa.Column('is_biodegradable', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_filaments_id'), 'filaments', ['id'], unique=False)

    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=128), nullable=True),
        sa.Column('avatar', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('avatar_updated_at', sa.DateTime(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('language', sa.String(), nullable=False, server_default='en'),
        sa.Column('theme', sa.String(), nullable=False, server_default='system'),
        sa.Column('role', sa.String(), nullable=False, server_default='user'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Audit logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('target', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)

    # Estimates
    op.create_table(
        'estimates',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('estimated_time', sa.Float(), nullable=False),
        sa.Column('estimated_cost', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_estimates_id'), 'estimates', ['id'], unique=False)

    # Filament pricing
    op.create_table(
        'filament_pricing',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('filament_id', sa.UUID(), sa.ForeignKey('filaments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('price_per_gram', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Models
    op.create_table(
        'models',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('thumbnail_url', sa.String(), nullable=True),
        sa.Column('geometry_hash', sa.String(), nullable=True, index=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('bbox', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('faces', sa.Integer(), nullable=True),
        sa.Column('vertices', sa.Integer(), nullable=True),
    )
    op.create_index(op.f('ix_models_id'), 'models', ['id'], unique=False)
    op.create_index(op.f('ix_models_geometry_hash'), 'models', ['geometry_hash'], unique=False)

    # Favorites
    op.create_table(
        'favorites',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('model_id', sa.UUID(), sa.ForeignKey('models.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_favorites_id'), 'favorites', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_favorites_id'), table_name='favorites')
    op.drop_table('favorites')

    op.drop_index(op.f('ix_models_geometry_hash'), table_name='models')
    op.drop_index(op.f('ix_models_id'), table_name='models')
    op.drop_table('models')

    op.drop_table('filament_pricing')

    op.drop_index(op.f('ix_estimates_id'), table_name='estimates')
    op.drop_table('estimates')

    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

    op.drop_index(op.f('ix_filaments_id'), table_name='filaments')
    op.drop_table('filaments')

    op.drop_table('estimate_settings')
