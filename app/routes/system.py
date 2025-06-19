import os
import time
import platform
import socket
import psutil
from datetime import datetime
from fastapi import APIRouter, Depends
from app.database import check_db_connection, async_session
from app.dependencies import get_current_user
from app.schemas import TokenData  # ✅ only if you're using TokenData

router = APIRouter(prefix="/system", tags=["System"])

START_TIME = time.time()

@router.get("/status", summary="System status check")
async def get_status(user: TokenData = Depends(get_current_user)):
    db_ok = await check_db_connection(async_session)
    return {
        "status": "ok",
        "db_connected": db_ok,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "host": socket.gethostname(),
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.get("/version", summary="API version info")
async def get_version():
    return {
        "version": os.getenv("API_VERSION", "dev"),
        "python_version": platform.python_version(),
        "platform": platform.system(),
    }

@router.get("/env", summary="Server environment snapshot (non-sensitive)")
async def get_env():
    return {
        "api_env": os.getenv("ENV", "development"),
        "worker_enabled": os.getenv("CELERY_ENABLED", "false"),
        "debug": os.getenv("DEBUG", "false"),
        "host": socket.gethostname(),
        "cpu": psutil.cpu_count(logical=True),
        "mem_gb": round(psutil.virtual_memory().total / 1024**3, 2),
    }

@router.get("/ping", summary="Simple healthcheck")
async def ping():
    return {"ping": "pong"}