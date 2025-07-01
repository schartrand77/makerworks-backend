from __future__ import with_statement

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from pathlib import Path

# ───────────────────────────────────────────────
# Force project root (/makerworks-backend) into sys.path
# ───────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ───────────────────────────────────────────────
# Load SQLAlchemy Base + Settings
# ───────────────────────────────────────────────
try:
    from app.models.models import Base  # ✅ Adjusted to actual structure
    from app.config.settings import settings
except ImportError as e:
    raise RuntimeError(f"❌ Failed to import Base/config: {e}")

# ───────────────────────────────────────────────
# Alembic Configuration
# ───────────────────────────────────────────────
config = context.config
fileConfig(config.config_file_name)

sqlalchemy_url = getattr(settings, "database_url", None) or os.environ.get("DATABASE_URL")
if not sqlalchemy_url:
    raise RuntimeError("❌ No DATABASE_URL found in settings or environment.")

config.set_main_option("sqlalchemy.url", sqlalchemy_url)
target_metadata = Base.metadata

# ───────────────────────────────────────────────
# Migration logic
# ───────────────────────────────────────────────
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=sqlalchemy_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# ───────────────────────────────────────────────
# Entrypoint
# ───────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()