import time
import socket
import platform
import psutil
import asyncpg
import redis.asyncio as redis
import pynvml
import logging
from datetime import datetime
from app.config.settings import settings

START_TIME = time.time()
logger = logging.getLogger("uvicorn")

def get_uptime() -> float:
    return round(time.time() - START_TIME, 2)

async def get_system_status_snapshot():
    """Return current backend system metrics for WebSocket streaming."""

    # ─── PostgreSQL Connectivity ──────────────────────────────
    try:
        import re
        raw_dsn = re.sub(r'\+asyncpg', '', settings.async_database_url)
        conn = await asyncpg.connect(raw_dsn)
        await conn.execute("SELECT 1")
        await conn.close()
        db_ok = True
    except Exception as e:
        db_ok = False
        logger.warning(f"⚠️ PostgreSQL connectivity check failed: {e}")

    # ─── Redis Connectivity ──────────────────────────────────
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_ok = await redis_client.ping()
    except Exception as e:
        redis_ok = False
        logger.warning(f"⚠️ Redis connectivity check failed: {e}")

    # ─── GPU Detection (NVML) ────────────────────────────────
    try:
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        gpus = [
            pynvml.nvmlDeviceGetName(pynvml.nvmlDeviceGetHandleByIndex(i)).decode()
            for i in range(gpu_count)
        ]
        pynvml.nvmlShutdown()
    except Exception as e:
        gpus = ["None Detected"]
        logger.warning(f"⚠️ GPU detection failed: {e}")

    # ─── Compose Snapshot ────────────────────────────────────
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": get_uptime(),
        "db_connected": db_ok,
        "redis_connected": redis_ok,
        "host": socket.gethostname(),
        "cpu_logical": psutil.cpu_count(logical=True),
        "mem_gb": round(psutil.virtual_memory().total / 1024**3, 2),
        "gpus": gpus,
        "authentik": True,  # TODO: Implement real status check
        "frontend_connected": True,  # TODO: Implement real ping check
    }

    return snapshot