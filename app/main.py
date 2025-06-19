from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import random

# Import routers
from app.routes import (
    auth,
    upload,
    models,
    filaments,
    users,
    system,
    favorites,
    checkout,
    admin,
)

from app.config import settings

# -----------------------------------------------------
# ✅ Initialize FastAPI app
# -----------------------------------------------------
app = FastAPI()

# -----------------------------------------------------
# ✅ Apply CORS middleware *before* mounting routes
# -----------------------------------------------------
origins = [
    "http://localhost:5173",
    "http://192.168.1.191:5173",   # Mac local IP
    "http://192.168.1.170:5173",   # Unraid local IP (raw)
    "http://192.168.1.170:49152",  # Unraid Docker port mapping
    "http://192.168.1.170:8000", 
     "http://100.72.184.28:5173",  # Original backend port (important for preflight!)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------
# ✅ Serve uploaded files (STLs, thumbnails, avatars)
# -----------------------------------------------------
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# -----------------------------------------------------
# ✅ Register API routes under /api/v1/*
# -----------------------------------------------------
app.include_router(auth.router,      prefix="/api/v1",           tags=["auth"])
app.include_router(upload.router,    prefix="/api/v1/upload",    tags=["upload"])
app.include_router(models.router,    prefix="/api/v1/models",    tags=["models"])
app.include_router(filaments.router, prefix="/api/v1/filaments", tags=["filaments"])
app.include_router(users.router,     prefix="/api/v1/users",     tags=["users"])
app.include_router(system.router,    prefix="/api/v1/system",    tags=["system"])
app.include_router(favorites.router, prefix="/api/v1/favorites", tags=["favorites"])
app.include_router(checkout.router,  prefix="/api/v1/checkout",  tags=["checkout"])
app.include_router(admin.router,     prefix="/api/v1/admin",     tags=["admin"])

# -----------------------------------------------------
# 🪩 Randomized startup banner
# -----------------------------------------------------
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
]

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info(random.choice(boot_messages))