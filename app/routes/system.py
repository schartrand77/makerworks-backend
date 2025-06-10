# In routes/system.py or add directly in main.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
def ping():
    return {"status": "ok", "message": "👋 Backend alive and well."}