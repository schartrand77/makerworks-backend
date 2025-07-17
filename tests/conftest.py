import os
import sys
from pathlib import Path

# Ensure test defaults are used
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DOMAIN", "http://testserver")
os.environ.setdefault("BASE_URL", "http://testserver")
os.environ.setdefault("VITE_API_BASE_URL", "http://testserver")
os.environ.setdefault("UPLOAD_DIR", "/tmp")
os.environ.setdefault("MODEL_DIR", "/tmp")
os.environ.setdefault("AVATAR_DIR", "/tmp")
os.environ.setdefault("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("AUTHENTIK_URL", "http://auth.example.com")
os.environ.setdefault("AUTHENTIK_ISSUER", "http://auth.example.com/issuer")
os.environ.setdefault("AUTHENTIK_CLIENT_ID", "dummy")
os.environ.setdefault("AUTHENTIK_CLIENT_SECRET", "dummy")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("DISCORD_CHANNEL_ID", "0")
os.environ.setdefault("DISCORD_BOT_TOKEN", "dummy")
os.environ.setdefault("DISCORD_WEBHOOK_URL", "http://example.com/webhook")
os.environ.setdefault("METRICS_API_KEY", "dummy")

# Ensure repository root is on sys.path for module imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

