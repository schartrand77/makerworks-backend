import os
import socket
from dotenv import load_dotenv
from typing import List
from functools import lru_cache

from pydantic import Field, AnyHttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ─────────────────────────────────────────────
# Load from local .env explicitly
# ─────────────────────────────────────────────
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        populate_by_name=True,
    )

    # ────────────────
    # ENVIRONMENT
    # ────────────────
    env: str = Field(..., alias="ENV")

    # ────────────────
    # DOMAIN + PUBLIC URLS
    # ────────────────
    domain: str = Field(..., alias="DOMAIN")
    base_url: str = Field(..., alias="BASE_URL")
    vite_api_base_url: str = Field(..., alias="VITE_API_BASE_URL")

    # ────────────────
    # FILE SYSTEM
    # ────────────────
    upload_dir: str = Field(..., alias="UPLOAD_DIR")
    model_dir: str = Field(..., alias="MODEL_DIR")
    avatar_dir: str = Field(..., alias="AVATAR_DIR")

    # ────────────────
    # DATABASE
    # ────────────────
    database_url: str = Field(..., alias="DATABASE_URL")
    async_database_url: str = Field(..., alias="ASYNC_DATABASE_URL")

    @property
    def database_url_sync(self) -> str:
        """Return the sync-compatible version for Alembic and legacy tooling."""
        return self.async_database_url.replace("+asyncpg", "")

    # ────────────────
    # REDIS
    # ────────────────
    redis_url: str = Field(..., alias="REDIS_URL")

    # ────────────────
    # AUTHENTIK / OIDC
    # ────────────────
    raw_authentik_url: str = Field(..., alias="AUTHENTIK_URL")
    authentik_client_id: str = Field(..., alias="AUTHENTIK_CLIENT_ID")
    authentik_client_secret: str = Field(..., alias="AUTHENTIK_CLIENT_SECRET")

    @property
    def authentik_url(self) -> str:
        hostname = self.raw_authentik_url.replace("http://", "").replace("https://", "").split(":")[0]
        try:
            socket.gethostbyname(hostname)
            return self.raw_authentik_url
        except socket.error:
            return "http://192.168.1.170:9000"  # fallback for dev

    # ────────────────
    # JWT Fallback / Legacy Support
    # ────────────────
    secret_key: str = Field(default="", alias="JWT_SECRET")
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    # ────────────────
    # STRIPE
    # ────────────────
    stripe_secret_key: str = Field(..., alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(..., alias="STRIPE_WEBHOOK_SECRET")

    # ────────────────
    # CORS
    # ────────────────
    cors_origins_raw: str = Field(default="", alias="CORS_ORIGINS")
    cors_origins: List[AnyHttpUrl] = []

    @model_validator(mode="after")
    def parse_cors_origins(cls, values):
        raw = values.cors_origins_raw
        if raw:
            values.cors_origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
        else:
            values.cors_origins = []
        return values

    # ────────────────
    # Monitoring / Prometheus
    # ────────────────
    metrics_api_key: str = Field(..., alias="METRICS_API_KEY")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()