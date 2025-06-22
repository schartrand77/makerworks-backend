import os
import random
import logging
from datetime import datetime

import psutil
import pynvml
import asyncpg
import redis.asyncio as redis

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, users, upload, system

# Initialize logger early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logging.getLogger(name).setLevel(logging.INFO)

# FastAPI instance
app = FastAPI(
    title="MakerWorks Backend",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://192.168.1.191:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup timestamp
START_TIME = datetime.utcnow()

class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

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

@app.on_event("startup")
async def log_boot_message():
    boot_message = random.choice(boot_messages)
    print(f"{Colors.CYAN}{boot_message}{Colors.RESET}")
    logger.info(f"{Colors.CYAN}{boot_message}{Colors.RESET}")

    # Async DB check
    try:
        raw_pg_url = settings.async_database_url
        if raw_pg_url.startswith("postgresql+asyncpg://"):
            raw_pg_url = raw_pg_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(dsn=raw_pg_url)
        await conn.close()
        db_status = f"{Colors.GREEN}✔ Connected{Colors.RESET}"
    except Exception as e:
        db_status = f"{Colors.YELLOW}⚠ DB ERROR: {str(e)}{Colors.RESET}"

    # Redis check
    try:
        r = redis.Redis.from_url(settings.redis_url)
        pong = await r.ping()
        redis_status = f"{Colors.GREEN}✔ Connected{Colors.RESET}" if pong else f"{Colors.YELLOW}⚠ Redis Unresponsive{Colors.RESET}"
    except Exception as e:
        redis_status = f"{Colors.YELLOW}⚠ Redis ERROR: {str(e)}{Colors.RESET}"

    # System stats
    mem = psutil.virtual_memory()
    cpu_count = psutil.cpu_count(logical=False)

    try:
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        gpu_names = ", ".join(
            pynvml.nvmlDeviceGetName(pynvml.nvmlDeviceGetHandleByIndex(i)).decode()
            for i in range(gpu_count)
        )
        pynvml.nvmlShutdown()
    except Exception:
        gpu_names = "None Detected"

    # Logging
    logger.info(f"{Colors.CYAN}🔗 DB Status:{Colors.RESET} {db_status}")
    logger.info(f"{Colors.CYAN}📡 Redis Status:{Colors.RESET} {redis_status}")
    logger.info(f"{Colors.CYAN}🖥️  CPU Cores:{Colors.RESET} {cpu_count}")
    logger.info(f"{Colors.CYAN}🧠 RAM:{Colors.RESET} {mem.total // (1024 ** 2)} MB")
    logger.info(f"{Colors.CYAN}🖼️  GPU(s):{Colors.RESET} {gpu_names}")
    logger.info(f"{Colors.CYAN}🌍 Environment:{Colors.RESET} {settings.env}")
    logger.info(f"{Colors.CYAN}⏱️  Uptime started:{Colors.RESET} {START_TIME.isoformat()} UTC")

print(f"{Colors.GREEN}✅ FastAPI booted on http://localhost:8000 (Press CTRL+C to stop){Colors.RESET}")

# Register routes
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(users.router, prefix="/api/v1/users")
app.include_router(upload.router, prefix="/api/v1/upload")
app.include_router(system.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)