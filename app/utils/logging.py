import logging
import os
import platform
import sys
import time

import psutil
import psycopg2
import redis
import requests  # type: ignore[import-untyped]
from prometheus_client import Gauge, Info
from psycopg2 import OperationalError

from app.utils.boot_messages import random_boot_message

try:
    import colorlog
except ImportError:
    colorlog = None

START_TIME = time.time()

logger = logging.getLogger("makerworks")
logger.setLevel(logging.INFO)


def configure_colorlog():
    """
    Configures the logger with colorlog if available.
    """
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if colorlog:
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s] [%(levelname)s]%(reset)s %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    else:
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)


# call it immediately to set up logging on import
configure_colorlog()


# ─────────── Prometheus Gauges ───────────
startup_time_gauge = Gauge(
    "makerworks_startup_seconds", "Time taken to start MakerWorks backend"
)
route_count_gauge = Gauge(
    "makerworks_route_count", "Total number of registered API routes"
)
redis_status_gauge = Gauge("makerworks_redis_up", "Redis availability (1=up, 0=down)")
postgres_status_gauge = Gauge(
    "makerworks_postgres_up", "PostgreSQL availability (1=up, 0=down)"
)
authentik_status_gauge = Gauge(
    "makerworks_authentik_up", "Authentik availability (1=up, 0=down)"
)
memory_used_gauge = Gauge("makerworks_memory_used_mb", "Memory used (in MB)")
memory_percent_gauge = Gauge("makerworks_memory_percent", "Percent memory used")
gpu_info = Info("makerworks_gpu", "GPU detected on system")

_previous_routes: set = set()


def check_redis_available(url: str) -> bool:
    try:
        r = redis.Redis.from_url(url, socket_connect_timeout=1)
        return r.ping()
    except Exception:
        return False


def check_postgres_available() -> bool:
    try:
        dsn = os.getenv("DATABASE_URL") or ""
        clean_dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
        conn = psycopg2.connect(clean_dsn, connect_timeout=1)
        conn.close()
        return True
    except OperationalError:
        return False


def check_authentik_available() -> bool:
    default_url = "http://authentik:9000/outpost.goauthentik.io/ping"
    fallback_url = "http://localhost:9000/outpost.goauthentik.io/ping"
    attempted_urls = []

    for url in [default_url, fallback_url]:
        attempted_urls.append(url)
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 204:
                logger.info(f"🛂 Authentik: Connected at {url}")
                return True
        except Exception as e:
            logger.debug(f"🛂 Authentik: Failed at {url} — {type(e).__name__}")

    logger.error(f"🛂 Authentik: Unreachable at {attempted_urls}")
    return False


def detect_gpu() -> str:
    # Improved GPU detection
    try:
        import subprocess

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        )
        gpus = [
            line.strip() for line in result.stdout.strip().splitlines() if line.strip()
        ]
        if gpus:
            return ", ".join(gpus)
    except Exception:
        pass

    if platform.system() == "Darwin" and platform.machine().startswith("arm"):
        return "Apple Metal"

    return "None"


def startup_banner(route_count: int | None = None, routes: list[str] | None = None):
    logger.info("🚀 MakerWorks Backend Started")
    logger.info(f"🖥️  Platform: {platform.system()} {platform.release()}")
    logger.info(f"🧠 CPU Cores: {os.cpu_count()}")

    mem = psutil.virtual_memory()
    mem_used_mb = mem.used // (1024**2)
    logger.info(
        f"📦 Memory: {mem_used_mb}MB used / {mem.total // (1024 ** 2)}MB total ({mem.percent}%)"
    )
    memory_used_gauge.set(mem_used_mb)
    memory_percent_gauge.set(mem.percent)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_status = check_redis_available(redis_url)
    logger.info(
        f"🧱 Redis: {'Connected' if redis_status else 'Unavailable'} ({redis_url})"
    )
    redis_status_gauge.set(1 if redis_status else 0)

    pg_status = check_postgres_available()
    logger.info(f"🗃️  PostgreSQL: {'Connected' if pg_status else 'Unavailable'}")
    postgres_status_gauge.set(1 if pg_status else 0)

    ak_status = check_authentik_available()
    logger.info(f"🛂 Authentik: {'Available' if ak_status else 'Unavailable'}")
    authentik_status_gauge.set(1 if ak_status else 0)

    gpu = detect_gpu()
    logger.info(f"🎮 GPU: {gpu}")
    gpu_info.info({"type": gpu})

    if route_count is not None:
        logger.info(f"📚 Registered Routes: {route_count}")
        route_count_gauge.set(route_count)

    global _previous_routes
    _previous_routes = set(routes or [])

    elapsed = time.time() - START_TIME
    logger.info(f"⏱️  Startup Time: {elapsed:.2f}s")
    startup_time_gauge.set(elapsed)

    logger.info(f"🎬 Boot Message: {random_boot_message()}")
