import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

dotenv_path = Path(__file__).resolve().parents[1] / ".env.dev"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"✅ Loaded environment from {dotenv_path}")
else:
    raise RuntimeError("❌ .env.dev not found")

from app.config.settings import settings
from app.models.models import Base

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

sqlalchemy_url = settings.database_url
if not sqlalchemy_url:
    raise RuntimeError("❌ DATABASE_URL is missing")

print(f"✅ Using DATABASE_URL: {sqlalchemy_url}")


def run_migrations_offline():
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
    connectable = create_engine(sqlalchemy_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
