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
from rich import print as rprint

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
        rprint("[bold green]✅ PostgreSQL connection successful[/bold green]")
    except Exception as e:
        rprint(f"[bold red]❌ PostgreSQL connection failed:[/bold red] {e}")

    # ─── Redis Connectivity ──────────────────────────────────
    try:
        redis_client = redis.from_url(settings.redis_url)
        if await redis_client.ping():
            snapshot["statuses"]["Redis"]["connected"] = True
            snapshot["statuses"]["Redis"]["color"] = "green"
            rprint("[bold green]✅ Redis ping successful[/bold green]")
    except Exception as e:
        rprint(f"[bold red]❌ Redis connection failed:[/bold red] {e}")

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
        rprint(f"[bold cyan]🖥️ Detected GPUs:[/bold cyan] {', '.join([g['name'] for g in gpus])}")
    except Exception as e:
        snapshot["gpus"] = [{"name": "None Detected", "color": "gray"}]
        rprint(f"[bold yellow]⚠️ GPU detection failed:[/bold yellow] {e}")

    # ─── Final Snapshot Print ────────────────────────────────
    rprint("\n[bold bright_white]📊 System Snapshot on Startup:[/bold bright_white]")
    rprint(f"[cyan]   timestamp[/cyan]: [white]{snapshot['timestamp']}[/white]")
    rprint(f"[cyan]   uptime_seconds[/cyan]: [white]{snapshot['uptime_seconds']}[/white]")
    rprint(f"[cyan]   host[/cyan]: [white]{snapshot['host']}[/white]")
    rprint(f"[cyan]   cpu_logical[/cyan]: [white]{snapshot['cpu_logical']}[/white]")
    rprint(f"[cyan]   mem_gb[/cyan]: [white]{snapshot['mem_gb']}[/white]")

    gpu_names = ', '.join([g['name'] for g in snapshot['gpus']])
    rprint(f"[cyan]   gpus[/cyan]: [white]{gpu_names}[/white]")

    rprint(f"[cyan]   statuses:[/cyan]")
    for name, stat in snapshot["statuses"].items():
        color = stat["color"]
        icon = "✅" if stat["connected"] else "❌"
        rprint(f"      [{color}]{icon} {name}[/]")

    return snapshot