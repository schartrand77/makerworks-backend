# /app/main.py

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.gzip import GZipMiddleware

from app.config.settings import settings
from app.routes import (
    admin,
    auth,
    avatar,
    cart,
    checkout,
    filaments,
    jwks,
    system,
    upload,
    users,
)
from app.utils.boot_messages import random_boot_message
from app.utils.system_info import get_system_status_snapshot

logger = logging.getLogger("uvicorn")


# ANSI colors
def cyan(text):
    return f"\033[96m{text}\033[0m"


def green(text):
    return f"\033[92m{text}\033[0m"


def yellow(text):
    return f"\033[93m{text}\033[0m"


def magenta(text):
    return f"\033[95m{text}\033[0m"


def gray(text):
    return f"\033[90m{text}\033[0m"


# ─── Create App ──────────────────────────────────────────────
app = FastAPI(title="MakerWorks API")

# ─── GZip Middleware ─────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── CORS Middleware ─────────────────────────────────────────
allowed_origins = settings.cors_origins or [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
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
    snapshot = get_system_status_snapshot()
    logger.info(green("📊 System Snapshot on Startup:"))
    for key, value in snapshot.items():
        logger.info(gray(f"   {key}: {value}"))


# ─── Route Registry Debug ────────────────────────────────────
@app.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    return JSONResponse([route.path for route in app.router.routes])


# ─── Boot Logging ─────────────────────────────────────────────
logger.info(f"{green('✅ CORS origins allowed:')} {allowed_origins}")
logger.info(f"{magenta('🎬 Boot Message:')} {random_boot_message()}")


# ─── Mount Helper ─────────────────────────────────────────────
def mount(router, prefix: str, tags: list[str]):
    app.include_router(router, prefix=prefix, tags=tags)
    logger.info(f"{cyan('🔌 Mounted:')} {prefix} — Tags: {yellow(', '.join(tags))}")


mount(auth.router, "/api/v1/auth", ["auth"])
mount(users.router, "/api/v1/users", ["users"])
mount(avatar.router, "/api/v1/users", ["users (avatar)"])
mount(system.router, "/api/v1/system", ["system"])
mount(upload.router, "/api/v1/upload", ["upload"])
mount(filaments.router, "/api/v1/filaments", ["filaments"])
mount(admin.router, "/api/v1/admin", ["admin"])
mount(cart.router, "/api/v1/cart", ["cart"])
mount(checkout.router, "/api/v1/checkout", ["checkout"])
mount(jwks.router, "", ["jwks"])


# ─── Print Route Table ───────────────────────────────────────
def print_route_table():
    table_header = f"\n{magenta('📋 Registered Routes:')}\n"
    print(table_header)
    print(f"{gray('METHOD'):<8} {gray('PATH')}")
    print(f"{'-'*8} {'-'*40}")
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ",".join(route.methods)
            path = route.path
            print(f"{green(methods):<8} {cyan(path)}")


print_route_table()
