# settings.py — MakerWorks Backend

from pydantic import BaseSettings
from functools import lru_cache
from typing import List
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger("uvicorn")

# Load environment variables from .env if available
load_dotenv()

class Settings(BaseSettings):
    env: str = "development"

    # ──────────────── Database and Cache ────────────────
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
    redis_url: str = "redis://localhost:6379"

    # ──────────────── Frontend Origins ────────────────
    frontend_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.170:5173",
        "http://192.168.1.191:5173",
        "http://100.72.184.28:5173",
        "https://makerworks.app"
    ]

    # ──────────────── Authentik OIDC (Public Cloudflare Tunnel) ────────────────
    authentik_issuer: str = "https://auth.makerworks.app/application/o"
    authentik_client_id: str = os.getenv("AUTHENTIK_CLIENT_ID", "")
    authentik_client_secret: str = os.getenv("AUTHENTIK_CLIENT_SECRET", "")
    authentik_audience: str = "makerworks"
    authentik_url: str = "https://auth.makerworks.app"

    # ──────────────── JWT (RS256) Signing ────────────────
    private_key_path: str = "keys/private.pem"
    private_key_kid: str = "makerworks-key-1"
    jwt_algorithm: str = "RS256"
    auth_audience: str = "https://makerworks.app"

    # Preloaded private key (optional)
    private_key: str = ""

    # ──────────────── Computed Properties ────────────────
    @property
    def cors_origins(self) -> List[str]:
        return self.frontend_origins

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Preload private key (only once)
        try:
            with open(self.private_key_path, "r") as f:
                self.private_key = f.read()
            logger.info(f"🔐 Loaded private key from {self.private_key_path}")
        except Exception as e:
            logger.warning(f"❌ Could not read private key: {e}")

        logger.info(f"🔧 Loaded settings for env: {self.env}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# ──────────────── Cached settings instance ────────────────
@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()