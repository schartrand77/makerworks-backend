# app/routes/ws_status.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.utils.auth.tokens import verify_jwt
from app.utils.system_info import get_system_status_snapshot
import asyncio

router = APIRouter()

@router.websocket("/system/status")
async def system_status_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = verify_jwt(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    try:
        while True:
            status_data = await get_system_status_snapshot()
            await websocket.send_json(status_data)
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass
