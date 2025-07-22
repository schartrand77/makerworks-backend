"""
System info utilities for MakerWorks.
"""

import os
import platform
import psutil
import sys
import time
import subprocess
import logging

logger = logging.getLogger("makerworks")

START_TIME = time.time()

# ────────────── TTY COLORS ──────────────
def is_tty() -> bool:
    return sys.stdout.isatty()


def color(text: str, code: str) -> str:
    if is_tty():
        return f"{code}{text}\033[0m"
    return text


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"

# ────────────── SYSTEM SNAPSHOT ──────────────
def get_system_status_snapshot() -> dict:
    """
    Return a minimal system status snapshot dict.
    """
    uptime_sec = time.time() - psutil.boot_time()
    try:
        load1, load5, load15 = os.getloadavg()
    except Exception:
        load1 = load5 = load15 = None

    gpu = detect_gpu()

    return {
        "platform": f"{platform.system()} {platform.release()}",
        "cpu_cores": psutil.cpu_count(),
        "memory_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "uptime_seconds": int(uptime_sec),
        "load_avg": {
            "1min": load1,
            "5min": load5,
            "15min": load15
        },
        "gpu": gpu
    }


# ────────────── GPU DETECTION ──────────────
def detect_gpu() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, check=True
        )
        gpus = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if gpus:
            return ", ".join(gpus)
    except Exception:
        pass

    try:
        import torch
        if torch.cuda.is_available():
            gpus = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
            if gpus:
                return ", ".join(gpus)
    except ImportError:
        pass

    if platform.system() == "Darwin" and platform.machine().startswith("arm"):
        return "Apple Metal"

    return "None"


# ────────────── STARTUP BANNER ──────────────
def startup_banner():
    """
    Logs a minimal, colorized system banner.
    """
    snap = get_system_status_snapshot()

    logger.info(color("🚀 MakerWorks Backend Started", GREEN))
    logger.info(f"{color('🖥️  Platform:', CYAN)} {snap['platform']} | CPU: {snap['cpu_cores']} cores")
    logger.info(f"{color('📦 Memory:', CYAN)} {snap['memory_gb']} GB total")
    logger.info(f"{color('⏳ Uptime:', CYAN)} {snap['uptime_seconds']//3600}h {(snap['uptime_seconds']//60)%60}m")
    if snap['load_avg']['1min'] is not None:
        logger.info(
            f"{color('📈 Load Average (1/5/15):', CYAN)} "
            f"{snap['load_avg']['1min']:.2f} / {snap['load_avg']['5min']:.2f} / {snap['load_avg']['15min']:.2f}"
        )
    logger.info(f"{color('🎮 GPU:', CYAN)} {snap['gpu']}")

    elapsed = time.time() - START_TIME
    logger.info(f"{color('⏱️  Startup Time:', CYAN)} {elapsed:.2f} seconds")
