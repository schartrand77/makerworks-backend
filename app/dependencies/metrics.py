from fastapi import Depends, HTTPException, Request, status
from app.config import settings

def verify_metrics_api_key(request: Request):
    key = request.headers.get("x-api-key")
    if key != settings.metrics_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key for /metrics",
        )