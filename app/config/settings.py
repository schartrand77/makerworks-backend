# app/config/settings.py

from functools import lru_cache
from pydantic import AnyHttpUrl, EmailStr, Field, ValidationError, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import sys


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

    # ─── JWT / Auth ─────────────────────────────────────────
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_secret: str = Field(default="secret", alias="JWT_SECRET")
    private_key_path: str | None = Field(default=None, alias="PRIVATE_KEY_PATH")
    public_key_path: str | None = Field(default=None, alias="PUBLIC_KEY_PATH")
    private_key_kid: str = Field(default="makerworks-key", alias="PRIVATE_KEY_KID")
    auth_audience: str = Field(default="makerworks", alias="AUTH_AUDIENCE")

    # ─── Authentik ──────────────────────────────────────────
    authentik_url: str = Field("", alias="AUTHENTIK_URL")
    authentik_issuer: str = Field("", alias="AUTHENTIK_ISSUER")
    authentik_client_id: str = Field("", alias="AUTHENTIK_CLIENT_ID")
    authentik_client_secret: str = Field("", alias="AUTHENTIK_CLIENT_SECRET")

    # ─── Stripe ─────────────────────────────────────────────
    stripe_secret_key: str = Field("", alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field("", alias="STRIPE_WEBHOOK_SECRET")

    # ─── Discord ────────────────────────────────────────────
    discord_channel_id: str = Field("", alias="DISCORD_CHANNEL_ID")
    discord_bot_token: str = Field("", alias="DISCORD_BOT_TOKEN")
    discord_webhook_url: str = Field("", alias="DISCORD_WEBHOOK_URL")

    # ─── Monitoring ─────────────────────────────────────────
    metrics_api_key: str = Field("", alias="METRICS_API_KEY")

    # ─── CORS ───────────────────────────────────────────────
    raw_cors_origins: str | list[AnyHttpUrl] = Field(default="", alias="CORS_ORIGINS")

    # ─── Optional ───────────────────────────────────────────
    bambu_ip: AnyHttpUrl | None = Field(None, alias="BAMBU_IP")
    permanent_admin_email: EmailStr | None = Field(None, alias="PERMANENT_ADMIN_EMAIL")

    @property
    def cors_origins(self) -> list[str]:
        if isinstance(self.raw_cors_origins, str):
            return [
                origin.strip()
                for origin in self.raw_cors_origins.split(",")
                if origin.strip()
            ]
        return list(self.raw_cors_origins)

    @validator("bambu_ip", pre=True)
    def validate_bambu_ip(cls, v):
        if not v:
            return None
        return v

    @validator("permanent_admin_email", pre=True)
    def validate_permanent_admin_email(cls, v):
        if not v:
            return None
        return v

    # Load env file dynamically
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore" if os.getenv("ENV", "development") == "development" else "forbid",
    )


@lru_cache
def get_settings() -> Settings:
    env_file = os.getenv("ENV_FILE", ".env")

    try:
        settings = Settings()
    except ValidationError as e:
        print(f"❌ Configuration validation error:\n{e}")
        sys.exit(1)

    print(f"✅ Loaded settings from `{env_file}` with ENV='{settings.env}'")

    # validate critical keys
    missing_keys = []
    if not settings.upload_dir:
        missing_keys.append("UPLOAD_DIR")
    if not settings.model_dir:
        missing_keys.append("MODEL_DIR")
    if not settings.avatar_dir:
        missing_keys.append("AVATAR_DIR")

    if missing_keys:
        print(f"❌ Missing required settings: {', '.join(missing_keys)}. Please check your `.env` or `.env.dev`.")
        sys.exit(1)

    return settings


settings = get_settings()
