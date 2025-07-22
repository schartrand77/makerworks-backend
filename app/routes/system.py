from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime

router = APIRouter()


@router.get("/status", tags=["system"], status_code=status.HTTP_200_OK)
async def system_status():
    """
    System status overview endpoint.
    """
    return JSONResponse(
        {
            "status": "ok",
            "message": "📈 System is up",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@router.get("/version", tags=["system"], status_code=status.HTTP_200_OK)
async def system_version():
    """
    Return the current application version.
    """
    return JSONResponse(
        {
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@router.get("/env", tags=["system"], status_code=status.HTTP_200_OK)
async def system_env():
    """
    Return environment variables snapshot (safe subset).
    """
    # Customize these as needed
    return JSONResponse(
        {
            "env": "development",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@router.get("/ping", tags=["system"], status_code=status.HTTP_200_OK)
async def system_ping():
    """
    Health check endpoint at /api/v1/system/ping
    """
    return JSONResponse(
        {
            "status": "ok",
            "message": "🏓 pong",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@router.post("/handshake", tags=["system"], status_code=status.HTTP_200_OK)
@router.get("/handshake", tags=["system"], status_code=status.HTTP_200_OK)
async def system_handshake():
    """
    Handshake endpoint at /api/v1/system/handshake
    """
    return JSONResponse(
        {
            "status": "ok",
            "message": "🤝 handshake successful",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
