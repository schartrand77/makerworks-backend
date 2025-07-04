import time
import socket
import platform
import psutil
import asyncpg
import redis.asyncio as redis
import pynvml
from datetime import datetime
from app.config import settings

START_TIME = time.time()

def get_uptime() -> float:
    return round(time.time() - START_TIME, 2)

async def get_system_status_snapshot():
    """Return current backend system metrics for WebSocket streaming."""
    # DB check
    try:
        import re
        raw_dsn = re.sub(r'\+asyncpg', '', settings.async_database_url)
        conn = await asyncpg.connect(raw_dsn)
        await conn.execute("SELECT 1")
        await conn.close()
        db_ok = True
    except:
        db_ok = False

    # Redis check
    try:
        r = redis.Redis.from_url(settings.redis_url)
        redis_ok = await r.ping()
    except:
        redis_ok = False

    # GPU check
    try:
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        gpus = [
            pynvml.nvmlDeviceGetName(pynvml.nvmlDeviceGetHandleByIndex(i)).decode()
            for i in range(gpu_count)
        ]
        pynvml.nvmlShutdown()
    except:
        gpus = ["None Detected"]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": get_uptime(),
        "db_connected": db_ok,
        "redis_connected": redis_ok,
        "host": socket.gethostname(),
        "cpu_logical": psutil.cpu_count(logical=True),
        "mem_gb": round(psutil.virtual_memory().total / 1024**3, 2),
        "gpus": gpus,
        "authentik": True,  # Static true until API ping check is implemented
        "frontend_connected": True,  # Static true unless dynamic tracking added
    }
