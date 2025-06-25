# main.py — MakerWorks Backend

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from prometheus_client import generate_latest

from app.routes import router as api_router
from app.routes import users, discord, ws_status, system, admin, jwks
from app.middleware.cors import add_cors  # ✅ FIXED
from app.config import settings
from app.utils.logging import startup_banner
from app.dependencies.metrics import verify_metrics_api_key

app = FastAPI(
    title="MakerWorks API",
    version="1.0.0",
    description="Backend for the MakerWorks platform (Auth: Authentik)",
)

# Apply CORS middleware
add_cors(app)

# Serve uploaded/static files
app.mount(
    "/static",
    StaticFiles(directory=settings.upload_dir, check_dir=False),
    name="static"
)

# API route includes
app.include_router(api_router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(discord.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
app.include_router(ws_status.router, prefix="/api/v1/ws", tags=["WebSocket"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(jwks.router, prefix="", tags=["JWKS"])


# Metrics route
@app.get("/metrics", include_in_schema=False)
def metrics(_: None = Depends(verify_metrics_api_key)):
    return Response(generate_latest(), media_type="text/plain")

# Exception handler to return 401 JSON instead of 302
@app.exception_handler(HTTPException)
async def handle_auth_redirects(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# Startup route log
@app.on_event("startup")
async def startup_event():
    routes = [
        f"{r.path} [{','.join(sorted(r.methods))}] → {r.name}"
        for r in app.routes if isinstance(r, APIRoute)
    ]
    startup_banner(route_count=len(routes), routes=routes)