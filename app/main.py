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
)

from app.config import settings  # <- Ensure config with UPLOAD_DIR exists

# Initialize app
app = FastAPI()

# Serve uploaded files (e.g. avatars, models)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# CORS middleware (adjust origins in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers with consistent /api prefix
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(filaments.router, prefix="/api/filaments", tags=["filaments"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(favorites.router, prefix="/api/favorites", tags=["favorites"])
app.include_router(checkout.router, prefix="/api/checkout", tags=["checkout"])

# 🪩 Boot banner — randomized per startup
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
