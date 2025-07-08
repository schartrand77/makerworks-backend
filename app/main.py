# /app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from app.config.settings import settings
from app.routes import (
    auth,
    users,
    system,
    filaments,
    upload,
    admin,
    cart,
    checkout,
)

from app.utils.boot_messages import random_boot_message
from app.utils.system_info import get_system_status_snapshot

import logging

logger = logging.getLogger("uvicorn")

# ─── Create App ──────────────────────────────────────────────
app = FastAPI(title="MakerWorks API")

# ─── GZip Middleware ─────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── CORS Middleware (Strict LAN-safe Origin Allowlist) ──────
allowed_origins = settings.cors_origins or [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.1.191:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Debug Middleware: Log Origin Headers ────────────────────
@app.middleware("http")
async def debug_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    logger.debug(f"[CORS] Incoming Origin: {origin}")
    return await call_next(request)

# ─── Lifecycle Hook: System Info Snapshot ────────────────────
@app.on_event("startup")
async def log_startup_system_info():
    snapshot = await get_system_status_snapshot()
    logger.info("📊 System Snapshot on Startup:")
    for key, value in snapshot.items():
        logger.info(f"   {key}: {value}")

@app.on_event("startup")
async def create_initial_admin():
    from app.utils.initial_admin import ensure_initial_admin
    await ensure_initial_admin()

# ─── Route Registry Debug ────────────────────────────────────
@app.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    return JSONResponse([route.path for route in app.router.routes])

# ─── Boot Logging ─────────────────────────────────────────────
logger.info(f"✅ CORS origins allowed: {allowed_origins}")
logger.info(f"🎬 Boot Message: {random_boot_message()}")

# ─── Include Routes ──────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
logger.info("🔌 Mounted: /api/v1/auth")

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
logger.info("🔌 Mounted: /api/v1/users")

app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
logger.info("🔌 Mounted: /api/v1/system")

app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
logger.info("🔌 Mounted: /api/v1/upload")

app.include_router(filaments.router, prefix="/api/v1/filaments", tags=["filaments"])
logger.info("🔌 Mounted: /api/v1/filaments")

app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
logger.info("🔌 Mounted: /api/v1/admin")

app.include_router(cart.router, prefix="/api/v1/cart", tags=["cart"])
logger.info("🔌 Mounted: /api/v1/cart")

app.include_router(checkout.router, prefix="/api/v1/checkout", tags=["checkout"])
logger.info("🔌 Mounted: /api/v1/checkout")