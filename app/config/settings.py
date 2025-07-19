from pydantic_settings import BaseSettings
from pydantic import ValidationError
from typing import List
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    async_database_url: str
    cors_origins: List[str] = ["http://localhost:5173"]
    env: str = "development"
    domain: str = "localhost"
    base_url: str = "http://localhost:8000"
    vite_api_base_url: str = "http://localhost:8000"
    database_url: str
    upload_dir: str = "uploads"
    model_dir: str = "models"
    avatar_dir: str = "avatars"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "changeme"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""  # ✅ added
    jwt_secret: str = "changeme"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env.dev"
        extra = "ignore"


try:
    settings = Settings()
    logger.info(f"✅ Loaded settings with CORS origins: {settings.cors_origins}")
except ValidationError as e:
    logger.critical(f"❌ Failed to load settings: {e}")
    raise


def get_settings() -> Settings:
    return settings