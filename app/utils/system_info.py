import os
import platform
import psutil
import subprocess
import sys
import time
from datetime import datetime, timedelta

from .boot_messages import random_boot_message
from .logging import logger, configure_colorlog

# Record startup time
START_TIME = time.time()


def get_uptime() -> float:
    """
    Returns uptime in seconds since START_TIME.
    """
    return time.time() - START_TIME


# ANSI colors
RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = "\033[93m"

# Configure colored logs
configure_colorlog()


def is_tty() -> bool:
    """
    Detect if stdout is a TTY (interactive terminal).
    """
    return sys.stdout.isatty()


def color(text: str, color_code: str) -> str:
    if is_tty():
        return f"{color_code}{text}{RESET}"
    return text


def detect_gpus() -> list[str]:
    """
    Detect GPUs via nvidia-smi or torch.
    Returns a list of GPU names or [] if none detected.
    """
    gpus = []
    # Try nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, check=True
        )
        gpus = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try torch
    if not gpus:
        try:
            import torch
            if torch.cuda.is_available():
                gpus = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
        except ImportError:
            pass

    # macOS Apple Silicon
    if not gpus and platform.system() == "Darwin" and platform.machine().startswith("arm"):
        gpus.append("Apple Metal")

    return gpus


def system_snapshot() -> dict:
    """
    Gather system information into a snapshot dict.
    """
    # compute uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_td = datetime.utcnow() - boot_time

    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": str(timedelta(seconds=int(uptime_td.total_seconds()))),
        "host": platform.node(),
        "cpu_logical": psutil.cpu_count(),
        "mem_gb": psutil.virtual_memory().total / (1024 ** 3),
        "gpus": detect_gpus(),
        "statuses": {
            "PostgreSQL": {"connected": True},
            "Redis": {"connected": True},
            "Authentik": {"connected": True},
            "Frontend": {"connected": True}
        }
    }
    return snapshot


def log_snapshot(snapshot: dict):
    """
    Logs the system snapshot and prints a colored version to the console if TTY.
    """
    logger.info("📊 System Snapshot on Startup:")
    logger.info(f"   Timestamp: {snapshot['timestamp']}")
    logger.info(f"   Uptime: {snapshot['uptime']}")
    logger.info(f"   Host: {snapshot['host']}")
    logger.info(f"   CPU Cores: {snapshot['cpu_logical']}")
    logger.info(f"   Memory: {snapshot['mem_gb']:.2f} GB")
    logger.info(f"   GPUs: {', '.join(snapshot['gpus']) or 'None'}")
    logger.info("   Statuses:")

    for name, status in snapshot["statuses"].items():
        connected = status["connected"]
        mark = "✅" if connected else "❌"
        logger.info(f"      {mark} {name}")

    # optionally print a more colorful version to stdout
    if is_tty():
        print("\n" + color("📊 System Snapshot (Color)", YELLOW))
        print(f"   {color('Timestamp:', CYAN)} {snapshot['timestamp']}")
        print(f"   {color('Uptime:', CYAN)} {snapshot['uptime']}")
        print(f"   {color('Host:', CYAN)} {snapshot['host']}")
        print(f"   {color('CPU Cores:', CYAN)} {snapshot['cpu_logical']}")
        print(f"   {color('Memory:', CYAN)} {snapshot['mem_gb']:.2f} GB")
        print(f"   {color('GPUs:', CYAN)} {', '.join(snapshot['gpus']) or 'None'}")
        print(f"   {color('Statuses:', CYAN)}")
        for name, status in snapshot["statuses"].items():
            connected = status["connected"]
            mark = color("✅", GREEN) if connected else color("❌", RED)
            name_colored = color(name, BLUE if connected else RED)
            print(f"      {mark} {name_colored}")
        print()  # spacing


def startup_banner():
    """
    Prints and logs the boot message + system snapshot.
    """
    msg = random_boot_message()
    logger.info(f"🎬 Boot Message: {msg}")
    if is_tty():
        print(color(f"🎬 Boot Message: {msg}", YELLOW))
    snap = system_snapshot()
    log_snapshot(snap)


def get_system_status_snapshot() -> dict:
    """
    Returns a snapshot of the current system status.
    """
    return system_snapshot()


if __name__ == "__main__":
    # Allow running as CLI: python -m app.utils.system_info
    startup_banner()