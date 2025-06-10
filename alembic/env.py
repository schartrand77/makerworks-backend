import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from dotenv import load_dotenv

# === Dynamically resolve root and import models ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Base

# === Load .env and config ===
load_dotenv()
config = context.config

# === Logging Setup ===
if config.config_file_name:
    fileConfig(config.config_file_name)

# === Set SQLAlchemy metadata for migrations ===
target_metadata = Base.metadata

# === Resolve database connection ===
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env or environment")

# === Online mode only ===
def run_migrations_online():
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # detects column type changes
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
