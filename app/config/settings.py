from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
import os


class Settings(BaseSettings):
    # App
    app_name: str = "MakerWorks API"
    env: str = "development"  # overridden by ENV

    # URLs
    domain: str = "http://localhost:8000"
    base_url: str = "http://localhost:8000"
    vite_api_base_url: Optional[str] = None

    # Database
    database_url: str

    # Storage
    uploads_path: Path = Path("uploads/")
    upload_dir: str = "uploads"
    model_dir: str = "models"
    avatar_dir: str = "avatars"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT (legacy)
    jwt_secret: Optional[str] = None
    jwt_algorithm: Optional[str] = None

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # Blender
    blender_path: Optional[str] = None
    use_gpu_for_blender: Optional[bool] = False

    # Admin seed
    admin_email: Optional[str] = None
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None

    # Monitoring
    grafana_admin_user: Optional[str] = None
    grafana_admin_password: Optional[str] = None
    flower_port: Optional[int] = None

    # CORS
    cors_origins: List[str] = ["*"]

    @property
    def debug(self) -> bool:
        return self.env.lower() == "development"

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
