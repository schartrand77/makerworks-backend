import os
import platform
import time
import psutil
import redis
import random
import psycopg2
import requests
from psycopg2 import OperationalError
from typing import Optional, List
from prometheus_client import Gauge, Info

from app.utils.boot_messages import random_boot_message  # ✅ now loaded from external file

# Time tracking for cold start
START_TIME = time.time()

class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    GREY = '\033[90m'
    BOLD = '\033[1m'

_previous_routes: set = set()

# ─────────── Prometheus Gauges ───────────
startup_time_gauge = Gauge("makerworks_startup_seconds", "Time taken to start MakerWorks backend")
route_count_gauge = Gauge("makerworks_route_count", "Total number of registered API routes")
redis_status_gauge = Gauge("makerworks_redis_up", "Redis availability (1=up, 0=down)")
postgres_status_gauge = Gauge("makerworks_postgres_up", "PostgreSQL availability (1=up, 0=down)")
authentik_status_gauge = Gauge("makerworks_authentik_up", "Authentik availability (1=up, 0=down)")
memory_used_gauge = Gauge("makerworks_memory_used_mb", "Memory used (in MB)")
memory_percent_gauge = Gauge("makerworks_memory_percent", "Percent memory used")
gpu_info = Info("makerworks_gpu", "GPU detected on system")

def check_redis_available(url: str) -> bool:
    try:
        r = redis.Redis.from_url(url, socket_connect_timeout=1)
        return r.ping()
    except Exception:
        return False

def check_postgres_available() -> bool:
    try:
        dsn = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(dsn, connect_timeout=1)
        conn.close()
        return True
    except OperationalError:
        return False

def check_authentik_available() -> bool:
    try:
        url = os.getenv("AUTHENTIK_USERINFO_URL", "http://192.168.1.170:9000/application/o/userinfo/")
        response = requests.options(url, timeout=2)
        return response.status_code in (200, 204)
    except Exception:
        return False

def detect_gpu() -> str:
    if os.system("nvidia-smi > /dev/null 2>&1") == 0:
        return "NVIDIA"
    if platform.system() == "Darwin" and platform.machine().startswith("arm"):
        return "Apple Metal"
    return "None"

def startup_banner(route_count: Optional[int] = None, routes: Optional[List[str]] = None):
    print(f"{Colors.OKGREEN}🚀 MakerWorks Backend Started{Colors.RESET}")
    print(f"{Colors.WARNING}🖥️  Platform: {platform.system()} {platform.release()}{Colors.RESET}")
    print(f"{Colors.WARNING}🧠 CPU Cores: {os.cpu_count()}{Colors.RESET}")

    # Memory
    mem = psutil.virtual_memory()
    mem_used_mb = mem.used // (1024 ** 2)
    print(f"{Colors.WARNING}📦 Memory: {mem_used_mb}MB used / {mem.total // (1024 ** 2)}MB total ({mem.percent}%) {Colors.RESET}")
    memory_used_gauge.set(mem_used_mb)
    memory_percent_gauge.set(mem.percent)

    # Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_status = check_redis_available(redis_url)
    redis_color = Colors.OKGREEN if redis_status else Colors.FAIL
    print(f"{redis_color}🧱 Redis: {'Connected' if redis_status else 'Unavailable'} ({redis_url}){Colors.RESET}")
    redis_status_gauge.set(1 if redis_status else 0)

    # PostgreSQL
    pg_status = check_postgres_available()
    pg_color = Colors.OKGREEN if pg_status else Colors.FAIL
    print(f"{pg_color}🗃️  PostgreSQL: {'Connected' if pg_status else 'Unavailable'}{Colors.RESET}")
    postgres_status_gauge.set(1 if pg_status else 0)

    # Authentik
    ak_status = check_authentik_available()
    ak_color = Colors.OKGREEN if ak_status else Colors.FAIL
    print(f"{ak_color}🛂 Authentik: {'Available' if ak_status else 'Unavailable'}{Colors.RESET}")
    authentik_status_gauge.set(1 if ak_status else 0)

    # GPU
    gpu = detect_gpu()
    gpu_color = Colors.OKGREEN if gpu != "None" else Colors.GREY
    print(f"{gpu_color}🎮 GPU: {gpu}{Colors.RESET}")
    gpu_info.info({'type': gpu})

    # Route summary
    global _previous_routes
    current_routes = set(routes or [])

    if route_count is not None:
        print(f"{Colors.CYAN}📚 Registered Routes: {route_count}{Colors.RESET}")
        route_count_gauge.set(route_count)

    if routes:
        print(f"{Colors.CYAN}📚 Route Map:{Colors.RESET}")
        for r in sorted(current_routes):
            prefix = "➕ " if r not in _previous_routes else "   "
            color = Colors.OKGREEN if r not in _previous_routes else Colors.GREY
            print(f"{color}{prefix}{r}{Colors.RESET}")

    _previous_routes = current_routes

    # Time taken
    elapsed = time.time() - START_TIME
    print(f"{Colors.CYAN}⏱️  Startup Time: {elapsed:.2f}s{Colors.RESET}")
    startup_time_gauge.set(elapsed)

    # Boot footer
    print(f"{Colors.BOLD}{Colors.CYAN}{random_boot_message()}{Colors.RESET}")