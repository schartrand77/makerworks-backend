import os
import platform
import socket
import logging
from datetime import datetime

import psutil
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session
from app.schemas.system import SystemStatus
from app.utils.system_info import get_uptime, START_TIME  # assumes these exist

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])


@router.get("/status", response_model=SystemStatus, summary="System status and DB check")
async def system_status():
    db_ok: bool = False

    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except SQLAlchemyError:
        logger.exception("Database connection failed")

    try:
        return SystemStatus(
            status="ok",
            db_connected=db_ok,
            uptime_seconds=get_uptime(),
            host=socket.gethostname(),
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception:
        logger.exception("Failed to construct system status response")
        raise


@router.get("/version", summary="API version and environment info")
async def get_version():
    return {
        "version": os.getenv("API_VERSION", "dev"),
        "python_version": platform.python_version(),
        "platform": platform.system(),
    }


@router.get("/env", summary="Non-sensitive environment metadata")
async def get_env():
    return {
        "api_env": os.getenv("ENV", "development"),
        "worker_enabled": os.getenv("CELERY_ENABLED", "false"),
        "debug": os.getenv("DEBUG", "false"),
        "host": socket.gethostname(),
        "cpu": psutil.cpu_count(logical=True),
        "mem_gb": round(psutil.virtual_memory().total / 1024**3, 2),
    }


@router.get("/ping", summary="Basic healthcheck")
async def ping():
    return {"ping": "pong"}