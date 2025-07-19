# /app/main.py

import logging

from contextlib import asynccontextmanager

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
    system,
    upload,
    users,
)
from app.utils.boot_messages import random_boot_message
from app.utils.system_info import get_system_status_snapshot

logger = logging.getLogger("uvicorn")

# ─── ANSI Colors ──────────────────────────────────────────────
def cyan(text): return f"\033[96m{text}\033[0m"
def green(text): return f"\033[92m{text}\033[0m"
def yellow(text): return f"\033[93m{text}\033[0m"
def magenta(text): return f"\033[95m{text}\033[0m"
def gray(text): return f"\033[90m{text}\033[0m"


# ─── App Factory ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    snapshot = get_system_status_snapshot()
    logger.info(green("📊 System Snapshot on Startup:"))
    for key, value in snapshot.items():
        logger.info(gray(f"   {key}: {value}"))

    # Print route table on startup
    print_route_table()

    yield

    # On shutdown (optional cleanup here)


app = FastAPI(
    title="MakerWorks API",
    lifespan=lifespan,
)

# ─── GZip Middleware ─────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── CORS Middleware ─────────────────────────────────────────
allowed_origins = settings.cors_origins or ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"{green('✅ CORS origins allowed:')} {allowed_origins}")
logger.info(f"{magenta('🎬 Boot Message:')} {random_boot_message()}")


# ─── Debug Middleware: Log Origin Headers ────────────────────
@app.middleware("http")
async def debug_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    logger.debug(f"[CORS] Incoming Origin: {origin}")
    return await call_next(request)


# ─── Debug Route: List Routes ─────────────────────────────────
@app.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    return JSONResponse([route.path for route in app.router.routes])


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


# ─── Print Route Table ───────────────────────────────────────
def print_route_table():
    header = f"\n{magenta('📋 Registered Routes:')}\n"
    print(header)
    print(f"{gray('METHODS'):<10} {gray('PATH')}")
    print(f"{'-'*10} {'-'*40}")
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ",".join(sorted(route.methods))
            path = route.path
            print(f"{green(methods):<10} {cyan(path)}")

