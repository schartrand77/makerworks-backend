# app/config/settings.py

from functools import lru_cache
from typing import List, Union
from pydantic import Field, AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ─── Core ───────────────────────────────────────────────
    env: str = Field(default="production", alias="ENV")
    domain: str = Field(..., alias="DOMAIN")
    base_url: str = Field(..., alias="BASE_URL")
    vite_api_base_url: str = Field(..., alias="VITE_API_BASE_URL")

    # ─── Paths ──────────────────────────────────────────────
    upload_dir: str = Field(..., alias="UPLOAD_DIR")
    model_dir: str = Field(..., alias="MODEL_DIR")
    avatar_dir: str = Field(..., alias="AVATAR_DIR")

    # ─── Database ───────────────────────────────────────────
    async_database_url: str = Field(..., alias="ASYNC_DATABASE_URL")
    database_url: str = Field(..., alias="DATABASE_URL")

    # ─── Redis / Celery ─────────────────────────────────────
    redis_url: str = Field("redis://localhost:6379", alias="REDIS_URL")

    # ─── JWT ────────────────────────────────────────────────
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    private_key_path: str = Field(default="./keys/private.pem", alias="PRIVATE_KEY_PATH")
    private_key_kid: str = Field(default="makerworks-key", alias="PRIVATE_KEY_KID")
    auth_audience: str = Field(default="makerworks", alias="AUTH_AUDIENCE")

    # ─── Stripe ─────────────────────────────────────────────
    stripe_secret_key: str = Field(..., alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(..., alias="STRIPE_WEBHOOK_SECRET")

    # ─── Discord ────────────────────────────────────────────
    discord_channel_id: str = Field(..., alias="DISCORD_CHANNEL_ID")
    discord_bot_token: str = Field(..., alias="DISCORD_BOT_TOKEN")
    discord_webhook_url: str = Field(..., alias="DISCORD_WEBHOOK_URL")

    # ─── Monitoring ─────────────────────────────────────────
    metrics_api_key: str = Field(..., alias="METRICS_API_KEY")

    # ─── Authentik ──────────────────────────────────────────
    authentik_url: str = Field(..., alias="AUTHENTIK_URL")
    authentik_issuer: str = Field(..., alias="AUTHENTIK_ISSUER")
    authentik_client_id: str = Field(..., alias="AUTHENTIK_CLIENT_ID")
    authentik_client_secret: str = Field(..., alias="AUTHENTIK_CLIENT_SECRET")

    # ─── CORS ───────────────────────────────────────────────
    raw_cors_origins: Union[str, List[AnyHttpUrl]] = Field(default="", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        if isinstance(self.raw_cors_origins, str):
            return [origin.strip() for origin in self.raw_cors_origins.split(",") if origin.strip()]
        return list(self.raw_cors_origins)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "forbid",  # Disallow undeclared environment variables
    }


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
print("[Debug] Effective CORS origins:", settings.cors_origins)