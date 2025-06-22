from __future__ import with_statement
import asyncio
import os
print("🔗 DB URL (Alembic):", os.environ.get("DATABASE_URL"))
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Ensure app module is on sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import Base
from app.config import settings

# ───────────────────────────────────────────────
# Alembic Config
# ───────────────────────────────────────────────
config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

# ✅ Use ASYNC URL for async engine
async_url = settings.async_database_url

# ✅ Use SYNC URL for offline mode
sync_url = settings.database_url_sync

# ───────────────────────────────────────────────
# OFFLINE MODE
# ───────────────────────────────────────────────
def run_migrations_offline():
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

# ───────────────────────────────────────────────
# ONLINE MODE (Async-safe)
# ───────────────────────────────────────────────
async def run_migrations_online():
    connectable = create_async_engine(async_url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        def do_migrations(sync_connection):
            context.configure(
                connection=sync_connection,
                target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(do_migrations)

# ───────────────────────────────────────────────
# Entrypoint
# ───────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())