# app/config.py

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Uploads
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent / "app/uploads")

    # JWT / Auth
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    JWT_SECRET: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # App domain
    DOMAIN: str

    # Database
    DATABASE_URL: str
    ASYNC_DATABASE_URL: str

    # Redis
    REDIS_URL: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # auto-populate JWT_SECRET from JWT_SECRET_KEY
        if not self.JWT_SECRET:
            self.JWT_SECRET = self.JWT_SECRET_KEY

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure upload directory exists to avoid crash during app.mount()
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)