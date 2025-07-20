from pydantic_settings import BaseSettings
from pydantic import ValidationError
from typing import List
from dotenv import load_dotenv
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Load .env.dev explicitly before anything else ───────────────
ENV_FILE = os.getenv("ENV_FILE", ".env.dev")
load_dotenv(ENV_FILE)
logger.info(f"✅ Loaded environment from {ENV_FILE}")


class Settings(BaseSettings):
    async_database_url: str = "postgresql+asyncpg://makerworks:makerworks@localhost:5432/makerworks"
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    env: str = "development"
    domain: str = "localhost"
    base_url: str = "http://localhost:8000"
    vite_api_base_url: str = "http://localhost:8000"
    database_url: str = "postgresql://makerworks:makerworks@localhost:5432/makerworks"
    upload_dir: str = "uploads"
    model_dir: str = "models"
    avatar_dir: str = "avatars"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "changeme"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    jwt_secret: str = "changeme"
    jwt_algorithm: str = "HS256"

    # ─── Blender path ───────────────────────────────
    blender_path: str = os.getenv("BLENDER_PATH", "/opt/homebrew/bin/blender")

    class Config:
        env_file = ENV_FILE
        extra = "ignore"

    @property
    def uploads_path(self) -> Path:
        """
        Returns the absolute path to the uploads directory,
        creating it if it doesn't exist.
        """
        path = Path(self.upload_dir).resolve()
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created missing uploads directory: {path}")
        else:
            logger.info(f"📁 uploads directory exists: {path}")
        return path


try:
    settings = Settings()
    logger.info(f"✅ Loaded settings with CORS origins: {settings.cors_origins}")
    logger.info(f"✅ Loaded async_database_url: {settings.async_database_url}")
    logger.info(f"✅ Using Blender binary: {settings.blender_path}")

    # ─── Sanity checks ───────────────────────────────
    if not settings.async_database_url:
        raise ValueError("❌ ASYNC_DATABASE_URL is missing from settings.")
    if "user" in settings.async_database_url and "makerworks" not in settings.async_database_url:
        logger.warning(f"⚠️ async_database_url seems misconfigured: {settings.async_database_url}")

    # Ensure uploads path is initialized at least once on startup
    _ = settings.uploads_path

except ValidationError as e:
    logger.critical(f"❌ Failed to load settings: {e}")
    raise
except Exception as e:
    logger.critical(str(e))
    raise


def get_settings() -> Settings:
    """
    Return the global settings instance.
    """
    return settings
