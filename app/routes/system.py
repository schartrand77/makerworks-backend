# app/routes/system.py

import os
import platform
import socket
import logging
import random
from datetime import datetime

import psutil
import asyncpg
import pynvml
import redis.asyncio as redis

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.system_info import get_uptime, START_TIME
from app.schemas.system import SystemStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["System"])

boot_messages = [
    "🧠 MakerWorks Backend online — thinking in polygons.",
    "🚀 Blender bots activated. Mesh metadata extraction commencing.",
    "🤖 Ready to judge your STL files mercilessly.",
    "📦 API online. Upload your 3D sins.",
    "🐙 Initializing tentacle subroutines... wait, wrong project.",
    "🛰️ Now serving files at ludicrous speed.",
    "🎨 Upload your .stl — we’ll make it pretty and smart.",
    "🔥 3D backend online. Please do not feed the render daemon.",
    "🧊 Cooling extruders... warming neurons.",
    "👁️‍🗨️ Scanning models for cursed topology.",
    "🧵 Loading spools of logic filament...",
    "🌌 Spinning up infinite detail.",
    "☁️ Fog of war clearing... Blender.exe found.",
    "🧽 Cleaning your meshes so you don’t have to.",
    "🧩 Snapping vertices into place like Lego gods.",
    "📐 Precision overkill enabled.",
    "🎯 Zero-micron tolerance activated.",
    "🧼 Autoclaving STL thoughts.",
    "🔍 Detecting overhangs... mocking silently.",
    "🔧 Backend secured. Time to break things (safely).",
    "🧑‍🏭 Print daemon stretching after long sleep.",
    "🎛️ Calibrating core alignment algorithms.",
    "🔁 Looping infinite infill.",
    "💬 Whispering to your slicer behind the scenes.",
    "📤 Ready to upload your printable dreams.",
    "🧱 Brick by virtual brick, reality is shaped.",
    "🦾 Activating mesh sentience circuits.",
    "🚦 Waiting at the intersection of triangles and torque.",
    "🧮 Recalculating print destiny...",
]

frontend_handshake_messages = [
    "🔗 Frontend linked. Time to make some prints!",
    "🧠 Frontend synced. All systems go.",
    "🎛️ Control panel online. Ready to deploy.",
    "🎨 UI handshake complete. Rendering vibes.",
    "🛸 MakerWorks frontend docked successfully.",
    "👾 Client uplink accepted. Let's create.",
    "🚀 Hello from the stars, frontend.",
    "🌐 Frontend handshake confirmed. Sync complete.",
    "🤝 Signal received. Building dreams in polygons.",
    "🔊 Broadcasting printer-core frequencies to UI.",
    "🧃 UI loaded like cold filament on a summer day.",
    "🦄 Frontend authenticated. Prepare for rainbow infill.",
    "🖥️ Frontend said hi. Backend says: hi back.",
    "🔒 Authentik handshake accepted. Welcome, commander.",
    "🔑 Token validated. You may proceed to production.",
    "📡 Identity lock from Authentik confirmed.",
    "💼 Authentik confirms identity. Opening job queue.",
    "🌟 Frontend handshake Authentikated™",
    "🕶️ Hello, Mr. Anderson. Authentik handshake accepted.",
    "📲 OAuth2 dance complete. The grid is yours."
]

@router.get("/status", summary="System diagnostics and boot info", response_model=SystemStatus)
async def system_status():
    # DB connectivity check
    try:
        import re
        raw_dsn = re.sub(r'\+asyncpg', '', settings.async_database_url)
        conn = await asyncpg.connect(raw_dsn)
        await conn.execute("SELECT 1")
        await conn.close()
        db_ok = True
    except Exception:
        db_ok = False
        logger.exception("Database connection failed")

    # Redis connectivity check
    try:
        r = redis.Redis.from_url(settings.redis_url)
        pong = await r.ping()
        redis_ok = bool(pong)
    except Exception:
        redis_ok = False
        logger.exception("Redis connection failed")

    # GPU detection
    try:
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        gpus = [
            pynvml.nvmlDeviceGetName(pynvml.nvmlDeviceGetHandleByIndex(i)).decode()
            for i in range(gpu_count)
        ]
        pynvml.nvmlShutdown()
    except Exception:
        gpus = ["None Detected"]

    return {
        "status": "ok" if db_ok else "degraded",
        "boot_message": random.choice(boot_messages),
        "db_connected": db_ok,
        "redis_connected": redis_ok,
        "uptime_seconds": get_uptime(),
        "uptime_start": datetime.fromtimestamp(START_TIME).isoformat(),
        "timestamp": datetime.utcnow().isoformat(),
        "host": socket.gethostname(),
        "cpu_cores": psutil.cpu_count(logical=False),
        "cpu_logical": psutil.cpu_count(logical=True),
        "memory_mb": round(psutil.virtual_memory().total / 1024**2),
        "gpus": gpus,
        "platform": platform.system(),
        "platform_version": platform.version(),
        "env": settings.env,
    }

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

# ─────────────────────────────────────────────────────────────
# Authenticated frontend-backend handshake
# ─────────────────────────────────────────────────────────────

def get_current_user(request: Request):
    if "Authorization" not in request.headers:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"username": "example-user"}
    
@router.post("/handshake", summary="Authenticated frontend-backend handshake (POST)")
async def frontend_handshake(user=Depends(get_current_user)):
    msg = random.choice(frontend_handshake_messages)
    return JSONResponse({"status": "ok", "user": user["username"], "message": msg})

@router.get("/handshake", summary="Authenticated frontend-backend handshake")
async def handshake(user=Depends(get_current_user)):
    msg = random.choice(frontend_handshake_messages)
    # logger.info(f"[🤝] Frontend handshake → {user['username']} → {msg}")
    return JSONResponse({"status": "ok", "user": user["username"], "message": msg})