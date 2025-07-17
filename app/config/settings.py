# app/config/settings.py

from functools import lru_cache

from pydantic import AnyHttpUrl, EmailStr, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ─── Core ───────────────────────────────────────────────
    env: str = Field(default="production", alias="ENV")
    domain: str | None = Field(None, alias="DOMAIN")
    base_url: str | None = Field(None, alias="BASE_URL")
    vite_api_base_url: str | None = Field(None, alias="VITE_API_BASE_URL")

    # ─── Paths ──────────────────────────────────────────────
    upload_dir: str | None = Field(None, alias="UPLOAD_DIR")
    model_dir: str | None = Field(None, alias="MODEL_DIR")
    avatar_dir: str | None = Field(None, alias="AVATAR_DIR")

    # ─── Database ───────────────────────────────────────────
    async_database_url: str | None = Field(None, alias="ASYNC_DATABASE_URL")
    database_url: str | None = Field(None, alias="DATABASE_URL")

    # ─── Redis / Celery ─────────────────────────────────────
    redis_url: str = Field("redis://localhost:6379", alias="REDIS_URL")

    # ─── JWT / Authentik ────────────────────────────────────
    jwt_algorithm: str = Field(default="RS256", alias="JWT_ALGORITHM")  # now RS256
    private_key_path: str | None = Field(default=None, alias="PRIVATE_KEY_PATH")  # optional if JWKS
    public_key_path: str | None = Field(default=None, alias="PUBLIC_KEY_PATH")    # optional if JWKS
    private_key_kid: str = Field(default="makerworks-key", alias="PRIVATE_KEY_KID")
    auth_audience: str = Field(default="makerworks", alias="AUTH_AUDIENCE")

    # ─── Authentik ──────────────────────────────────────────
    authentik_url: str | None = Field(None, alias="AUTHENTIK_URL")
    authentik_issuer: str | None = Field(None, alias="AUTHENTIK_ISSUER")
    authentik_client_id: str | None = Field(None, alias="AUTHENTIK_CLIENT_ID")
    authentik_client_secret: str | None = Field(None, alias="AUTHENTIK_CLIENT_SECRET")

    # ─── Stripe ─────────────────────────────────────────────
    stripe_secret_key: str | None = Field(None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str | None = Field(None, alias="STRIPE_WEBHOOK_SECRET")

    # ─── Discord ────────────────────────────────────────────
    discord_channel_id: str | None = Field(None, alias="DISCORD_CHANNEL_ID")
    discord_bot_token: str | None = Field(None, alias="DISCORD_BOT_TOKEN")
    discord_webhook_url: str | None = Field(None, alias="DISCORD_WEBHOOK_URL")

    # ─── Monitoring ─────────────────────────────────────────
    metrics_api_key: str | None = Field(None, alias="METRICS_API_KEY")

    # ─── CORS ───────────────────────────────────────────────
    raw_cors_origins: str | list[AnyHttpUrl] = Field(default="", alias="CORS_ORIGINS")

    # ─── Bambu ──────────────────────────────────────────────
    bambu_ip: AnyHttpUrl | None = Field(None, alias="BAMBU_IP")

    # ─── Permanent Admin (email only for record keeping) ───
    permanent_admin_email: EmailStr | None = Field(None, alias="PERMANENT_ADMIN_EMAIL")

    @model_validator(mode="after")
    def _test_defaults(cls, values: "Settings") -> "Settings":
        if values.env == "test":
            values.domain = values.domain or "http://testserver"
            values.base_url = values.base_url or "http://testserver"
            values.vite_api_base_url = values.vite_api_base_url or "http://testserver"
            values.upload_dir = values.upload_dir or "/tmp"
            values.model_dir = values.model_dir or "/tmp"
            values.avatar_dir = values.avatar_dir or "/tmp"
            values.async_database_url = values.async_database_url or "sqlite+aiosqlite:///:memory:"
            values.database_url = values.database_url or "sqlite:///:memory:"
            values.authentik_url = values.authentik_url or "http://auth.example.com"
            values.authentik_issuer = values.authentik_issuer or "http://auth.example.com/issuer"
            values.authentik_client_id = values.authentik_client_id or "dummy"
            values.authentik_client_secret = values.authentik_client_secret or "dummy"
            values.stripe_secret_key = values.stripe_secret_key or "sk_test_dummy"
            values.stripe_webhook_secret = values.stripe_webhook_secret or "whsec_dummy"
            values.discord_channel_id = values.discord_channel_id or "0"
            values.discord_bot_token = values.discord_bot_token or "dummy"
            values.discord_webhook_url = values.discord_webhook_url or "http://example.com/webhook"
            values.metrics_api_key = values.metrics_api_key or "dummy"
        return values

    @property
    def cors_origins(self) -> list[str]:
        if isinstance(self.raw_cors_origins, str):
            return [
                origin.strip()
                for origin in self.raw_cors_origins.split(",")
                if origin.strip()
            ]
        return list(self.raw_cors_origins)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "forbid",  # Disallow undeclared environment variables
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
