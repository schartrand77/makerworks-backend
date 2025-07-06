import os
import platform
import time
import psutil
import redis
import uuid
import psycopg2
import requests
import logging
from psycopg2 import OperationalError
from typing import Optional, List
from prometheus_client import Gauge, Info

from app.utils.boot_messages import random_boot_message

START_TIME = time.time()


# ─────────── Terminal Colors ───────────
class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    GREY = '\033[90m'
    BOLD = '\033[1m'


# ─────────── Colored Formatter ───────────
class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: Colors.GREY,
        logging.INFO: Colors.OKGREEN,
        logging.WARNING: Colors.WARNING,
        logging.ERROR: Colors.FAIL,
        logging.CRITICAL: Colors.BOLD + Colors.FAIL,
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)
        message = super().format(record)
        return f"{color}{message}{Colors.RESET}"


# ─────────── Structured Logger ───────────
logger = logging.getLogger("makerworks")
logger.setLevel(logging.INFO)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = ColorFormatter("[%(asctime)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ─────────── Prometheus Gauges ───────────
startup_time_gauge = Gauge("makerworks_startup_seconds", "Time taken to start MakerWorks backend")
route_count_gauge = Gauge("makerworks_route_count", "Total number of registered API routes")
redis_status_gauge = Gauge("makerworks_redis_up", "Redis availability (1=up, 0=down)")
postgres_status_gauge = Gauge("makerworks_postgres_up", "PostgreSQL availability (1=up, 0=down)")
authentik_status_gauge = Gauge("makerworks_authentik_up", "Authentik availability (1=up, 0=down)")
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
        dsn = os.getenv("DATABASE_URL")
        clean_dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
        conn = psycopg2.connect(clean_dsn, connect_timeout=1)
        conn.close()
        return True
    except OperationalError:
        return False


def check_authentik_available() -> bool:
    default_url = "http://authentik:9000/outpost.goauthentik.io/ping"
    fallback_url = "http://192.168.1.170:9000/outpost.goauthentik.io/ping"
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
    if os.system("nvidia-smi > /dev/null 2>&1") == 0:
        return "NVIDIA"
    if platform.system() == "Darwin" and platform.machine().startswith("arm"):
        return "Apple Metal"
    return "None"


def startup_banner(route_count: Optional[int] = None, routes: Optional[List[str]] = None):
    logger.info("🚀 MakerWorks Backend Started")
    logger.info(f"🖥️  Platform: {platform.system()} {platform.release()}")
    logger.info(f"🧠 CPU Cores: {os.cpu_count()}")

    mem = psutil.virtual_memory()
    mem_used_mb = mem.used // (1024 ** 2)
    logger.info(f"📦 Memory: {mem_used_mb}MB used / {mem.total // (1024 ** 2)}MB total ({mem.percent}%)")
    memory_used_gauge.set(mem_used_mb)
    memory_percent_gauge.set(mem.percent)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_status = check_redis_available(redis_url)
    logger.info(f"🧱 Redis: {'Connected' if redis_status else 'Unavailable'} ({redis_url})")
    redis_status_gauge.set(1 if redis_status else 0)

    pg_status = check_postgres_available()
    logger.info(f"🗃️  PostgreSQL: {'Connected' if pg_status else 'Unavailable'}")
    postgres_status_gauge.set(1 if pg_status else 0)

    ak_status = check_authentik_available()
    logger.info(f"🛂 Authentik: {'Available' if ak_status else 'Unavailable'}")
    authentik_status_gauge.set(1 if ak_status else 0)

    gpu = detect_gpu()
    logger.info(f"🎮 GPU: {gpu}")
    gpu_info.info({'type': gpu})

    if route_count is not None:
        logger.info(f"📚 Registered Routes: {route_count}")
        route_count_gauge.set(route_count)

    global _previous_routes
    _previous_routes = set(routes or [])

    elapsed = time.time() - START_TIME
    logger.info(f"⏱️  Startup Time: {elapsed:.2f}s")
    startup_time_gauge.set(elapsed)

    logger.info(f"{random_boot_message()}")