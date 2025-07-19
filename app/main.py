from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware
from app.utils.boot_messages import random_boot_message
from app.utils.system_info import get_system_status_snapshot
from app.config.settings import settings
import logging

logger = logging.getLogger("uvicorn")

# ─── App ─────────────────────────────────────
app = FastAPI(
    title="MakerWorks API",
)


# ─── Add Middleware *before* app starts ─────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# ─── Lifespan tasks ─────────────────────────
from contextlib import asynccontextmanager
from fastapi.routing import APIRoute

@asynccontextmanager
async def lifespan(app: FastAPI):
    snapshot = get_system_status_snapshot()
    logger.info("📊 System Snapshot on Startup:")
    for key, value in snapshot.items():
        logger.info(f"   {key}: {value}")

    logger.info(f"✅ CORS origins allowed: {settings.cors_origins}")
    logger.info(f"🎬 Boot Message: {random_boot_message()}")

    print_route_table()
    yield


app.router.lifespan_context = lifespan


# ─── Debug CORS Middleware ──────────────────
@app.middleware("http")
async def debug_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    logger.debug(f"[CORS] Incoming Origin: {origin}")
    return await call_next(request)


# ─── Debug Routes Endpoint ──────────────────
@app.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    return JSONResponse([route.path for route in app.router.routes])


# ─── Route Mount Helper ─────────────────────
def mount(router, prefix: str, tags: list[str]):
    app.include_router(router, prefix=prefix, tags=tags)
    logger.info(f"🔌 Mounted: {prefix} — Tags: {', '.join(tags)}")


# ─── Mount All Routes ───────────────────────
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

mount(auth.router, "/api/v1/auth", ["auth"])
mount(users.router, "/api/v1/users", ["users"])
mount(avatar.router, "/api/v1/users", ["users (avatar)"])
mount(system.router, "/api/v1/system", ["system"])
mount(upload.router, "/api/v1/upload", ["upload"])
mount(filaments.router, "/api/v1/filaments", ["filaments"])
mount(admin.router, "/api/v1/admin", ["admin"])
mount(cart.router, "/api/v1/cart", ["cart"])
mount(checkout.router, "/api/v1/checkout", ["checkout"])


# ─── Route Table Printer ────────────────────
def print_route_table():
    header = "\n📋 Registered Routes:\n"
    print(header)
    print(f"{'METHODS':<10} {'PATH'}")
    print(f"{'-'*10} {'-'*40}")
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ",".join(sorted(route.methods))
            path = route.path
            print(f"{methods:<10} {path}")