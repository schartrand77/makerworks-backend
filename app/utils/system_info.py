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
    """Return current backend system metrics for WebSocket streaming and logs."""

    # ─── Compose Snapshot ────────────────────────────────────
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": get_uptime(),
        "host": socket.gethostname(),
        "cpu_logical": psutil.cpu_count(logical=True),
        "mem_gb": round(psutil.virtual_memory().total / 1024**3, 2),
        "gpus": [],
        "statuses": {
            "PostgreSQL": {"connected": False, "color": "red"},
            "Redis": {"connected": False, "color": "red"},
            "Authentik": {"connected": True, "color": "cyan"},
            "Frontend": {"connected": True, "color": "blue"}
        }
    }

    # ─── PostgreSQL Connectivity ──────────────────────────────
    try:
        import re
        raw_dsn = re.sub(r'\+asyncpg', '', settings.async_database_url)
        conn = await asyncpg.connect(raw_dsn)
        await conn.execute("SELECT 1")
        await conn.close()
        snapshot["statuses"]["PostgreSQL"]["connected"] = True
        snapshot["statuses"]["PostgreSQL"]["color"] = "green"
        logger.info("✅ PostgreSQL connection successful")
    except Exception as e:
        logger.error("❌ PostgreSQL connection failed: %s", e)

    # ─── Redis Connectivity ──────────────────────────────────
    try:
        redis_client = redis.from_url(settings.redis_url)
        if await redis_client.ping():
            snapshot["statuses"]["Redis"]["connected"] = True
            snapshot["statuses"]["Redis"]["color"] = "green"
            logger.info("✅ Redis ping successful")
    except Exception as e:
        logger.error("❌ Redis connection failed: %s", e)

    # ─── GPU Detection (NVML) ────────────────────────────────
    try:
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        gpus = []
        for i in range(gpu_count):
            raw_name = pynvml.nvmlDeviceGetName(pynvml.nvmlDeviceGetHandleByIndex(i))
            name = raw_name.decode() if isinstance(raw_name, bytes) else str(raw_name)
            gpus.append({"name": name, "color": "teal"})
        pynvml.nvmlShutdown()
        snapshot["gpus"] = gpus
        logger.info("🖥️ Detected GPUs: %s", ', '.join([g['name'] for g in gpus]))
    except Exception as e:
        snapshot["gpus"] = [{"name": "None Detected", "color": "gray"}]
        logger.warning("⚠️ GPU detection failed: %s", e)

    # ─── Final Snapshot Print ────────────────────────────────
    logger.info("📊 System Snapshot on Startup:")
    logger.info("   timestamp: %s", snapshot['timestamp'])
    logger.info("   uptime_seconds: %s", snapshot['uptime_seconds'])
    logger.info("   host: %s", snapshot['host'])
    logger.info("   cpu_logical: %s", snapshot['cpu_logical'])
    logger.info("   mem_gb: %s", snapshot['mem_gb'])

    gpu_names = ', '.join([g['name'] for g in snapshot['gpus']])
    logger.info("   gpus: %s", gpu_names)

    logger.info("   statuses:")
    for name, stat in snapshot["statuses"].items():
        color = stat["color"]
        icon = "✅" if stat["connected"] else "❌"
        logger.info("      %s %s", icon, name)

    return snapshot
