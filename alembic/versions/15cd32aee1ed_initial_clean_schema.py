"""initial clean schema with seeded filaments

Revision ID: 15cd32aee1ed
Revises: 
Create Date: 2025-07-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pathlib import Path
from sqlalchemy import text
from uuid import uuid4
import json

# revision identifiers, used by Alembic.
revision: str = '15cd32aee1ed'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- SCHEMA CREATION ---
    op.create_table('estimate_settings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('custom_text_base_cost', sa.Float(), nullable=True),
        sa.Column('custom_text_cost_per_char', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('filaments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('variant', sa.String(), nullable=True),  # ✅ added
        sa.Column('subtype', sa.String(), nullable=True),
        sa.Column('surface', sa.String(), nullable=True),
        sa.Column('texture', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=False),
        sa.Column('color_name', sa.String(), nullable=True),
        sa.Column('price_per_kg', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_biodegradable', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(length=128), nullable=False),
        sa.Column('avatar', sa.String(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('theme', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_user_email'),
        sa.UniqueConstraint('username', name='uq_user_username')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    op.create_table('audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('filament_pricing',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filament_id', sa.String(), nullable=False),
        sa.Column('price_per_gram', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['filament_id'], ['filaments.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('models',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('filepath', sa.String(), nullable=False),
        sa.Column('preview_image', sa.String(), nullable=True),
        sa.Column('uploader', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('tags', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('volume_mm3', sa.Float(), nullable=True),
        sa.Column('dimensions_mm', sa.JSON(), nullable=True),
        sa.Column('face_count', sa.Integer(), nullable=True),
        sa.Column('geometry_hash', sa.String(length=64), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['uploader'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_models_geometry_hash'), 'models', ['geometry_hash'], unique=True)

    op.create_table('estimates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.Column('estimated_cost', sa.Float(), nullable=False),
        sa.Column('estimated_time', sa.Float(), nullable=False),
        sa.Column('is_paid', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['models.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('favorites',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['models.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'model_id', name='uq_user_model_favorite')
    )

    # --- SEED FILAMENTS ---
    print("📄 Loading and seeding filaments…")
    json_path = Path(__file__).parent / '../data/filaments.json'
    json_path = json_path.resolve()
    if not json_path.exists():
        raise FileNotFoundError(f"❌ JSON file not found at {json_path}")

    with open(json_path) as f:
        data = json.load(f)

    filaments = data.get("filaments", [])
    print(f"📦 Loaded {len(filaments)} filament definitions.")

    inserts = []
    for f in filaments:
        for color in f["colors"]:
            inserts.append({
                'id': str(uuid4()),
                'name': color,
                'variant': f["variant"],
                'price_per_kg': f["price_cad_per_kg"],
                'color': "#000000",  # placeholder — replace if needed
                'description': None,
                'is_active': True,
                'type': f["material"],
                'subtype': None,
                'surface': None,
                'texture': None,
                'color_name': color,
                'currency': "CAD",
                'is_biodegradable': False,
            })

    conn = op.get_bind()

    sql = text("""
        INSERT INTO filaments
            (id, name, variant, price_per_kg, color, description, is_active, type, subtype, surface, texture, color_name, currency, is_biodegradable)
        VALUES
            (:id, :name, :variant, :price_per_kg, :color, :description, :is_active, :type, :subtype, :surface, :texture, :color_name, :currency, :is_biodegradable)
    """)

    for idx, row in enumerate(inserts, 1):
        conn.execute(sql, row)
        if idx % 50 == 0 or idx == len(inserts):
            print(f"   … inserted {idx}/{len(inserts)} rows")

    print("✅ All filaments inserted successfully.")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('favorites')
    op.drop_table('estimates')
    op.drop_index(op.f('ix_models_geometry_hash'), table_name='models')
    op.drop_table('models')
    op.drop_table('filament_pricing')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    op.drop_table('filaments')
    op.drop_table('estimate_settings')