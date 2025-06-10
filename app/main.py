import random
from fastapi import FastAPI

from app.routes import (
    auth,
    upload,
    models,
    filaments,
    users,
    system,
    favorites,
    checkout,  # ← Stripe checkout routes
)

app = FastAPI(title="MakerWorks Backend")

# Register API routes
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(models.router, prefix="/api")
app.include_router(filaments.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(favorites.router, prefix="/api")
app.include_router(checkout.router, prefix="/api")  # ← Stripe session + webhook

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

print("\n" + random.choice(boot_messages) + "\n")