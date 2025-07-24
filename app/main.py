import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from app.config.settings import settings
from app.db.database import init_db
from app.routes import (
    admin,
    auth,
    avatar,
    cart,
    checkout,
    filaments,
    models,
    metrics,
    system,
    upload,
    users,
)
from app.services.cache.redis_service import verify_redis_connection
from app.startup.admin_seed import ensure_admin_user
from app.utils.boot_messages import random_boot_message
from app.utils.system_info import get_system_status_snapshot

logger = logging.getLogger("uvicorn")

# ─── App ─────────────────────────────────────
app = FastAPI(
    title="MakerWorks API",
    version="1.0.0",
    description="MakerWorks backend API",
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
@asynccontextmanager
async def lifespan(app: FastAPI):
    snapshot = get_system_status_snapshot()
    logger.info("📊 System Snapshot on Startup:")
    for key, value in snapshot.items():
        logger.info(f"   {key}: {value}")

    logger.info(f"✅ CORS origins allowed: {settings.cors_origins}")
    logger.info(f"🎬 Boot Message: {random_boot_message()}")

    await verify_redis_connection()
    await init_db()
    await ensure_admin_user()

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
    """
    Returns a list of all registered routes with methods, path, name, and tags.
    """
    routes_info = []
    for route in app.router.routes:
        routes_info.append({
            "path": getattr(route, "path", None),
            "name": getattr(route, "name", None),
            "methods": list(getattr(route, "methods", [])),
            "tags": getattr(route, "tags", []),
        })
    return JSONResponse(routes_info)

# ─── Route Mount Helper ─────────────────────
def mount(router, prefix: str, tags: list[str]):
    app.include_router(router, prefix=prefix, tags=tags)
    logger.info(f"🔌 Mounted: {prefix or '/'} — Tags: {', '.join(tags)}")

# ─── Mount All Routes ───────────────────────

mount(auth.router, "/api/v1/auth", ["auth"])
mount(users.router, "/api/v1/users", ["users"])
mount(avatar.router, "", ["avatar"])  # avatar.py already has prefix /api/v1/avatar
mount(system.router, "/api/v1/system", ["system"])
mount(upload.router, "/api/v1/upload", ["upload"])
mount(filaments.router, "/api/v1/filaments", ["filaments"])
mount(admin.router, "/api/v1/admin", ["admin"])
mount(cart.router, "/api/v1/cart", ["cart"])

if settings.stripe_secret_key:
    mount(checkout.router, "/api/v1/checkout", ["checkout"])
else:
    logger.warning("⚠️ STRIPE_SECRET_KEY is not set. Checkout routes not mounted.")

mount(models.router, "/api/v1/models", ["models"])
mount(metrics.router, "/metrics", ["metrics"])
# 🔷 Discord route removed here.

# ─── Mount Static Files ─────────────────────
uploads_path = settings.uploads_path

if not uploads_path.exists():
    uploads_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Created uploads directory at: {uploads_path}")
else:
    logger.info(f"📁 Uploads directory exists: {uploads_path}")

app.mount(
    "/uploads",
    StaticFiles(directory=uploads_path),
    name="uploads"
)
logger.info(f"📁 Uploads served from {uploads_path} at /uploads")
