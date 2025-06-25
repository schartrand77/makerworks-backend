from fastapi import APIRouter, HTTPException, Request, Response, status, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Set
import httpx
import os
import logging
import asyncio

from app.dependencies.auth import get_current_admin_user

router = APIRouter()
logger = logging.getLogger("makerworks.discord")

DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# WebSocket clients
active_connections: Set[WebSocket] = set()


# Fetch recent messages from Discord channel
async def fetch_discord_messages(limit: int = 5) -> List[Dict]:
    if not DISCORD_CHANNEL_ID or not DISCORD_BOT_TOKEN:
        logger.error("Missing DISCORD_CHANNEL_ID or DISCORD_BOT_TOKEN")
        raise HTTPException(status_code=500, detail="Missing Discord config")

    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, headers=headers, params={"limit": limit})
            res.raise_for_status()
            messages = res.json()
            return [
                {
                    "author": msg.get("author", {}).get("username", "Unknown"),
                    "content": msg.get("content", "")
                }
                for msg in messages
            ]
        except httpx.HTTPStatusError as e:
            logger.error(f"Discord API HTTP error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=502, detail="Discord API error")
        except Exception as e:
            logger.exception("Unhandled exception while fetching Discord feed")
            raise HTTPException(status_code=500, detail="Internal server error")


# GET latest messages (public route or protect if needed)
@router.get("/discord/feed", status_code=200)
async def get_discord_feed():
    return await fetch_discord_messages()


# WebSocket: real-time broadcast to connected clients
@router.websocket("/ws/discord/feed")
async def websocket_discord_feed(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    logger.info("WebSocket client connected for Discord feed")

    try:
        while True:
            messages = await fetch_discord_messages()
            for conn in list(active_connections):
                try:
                    await conn.send_json(messages)
                except WebSocketDisconnect:
                    active_connections.remove(conn)
                    logger.info("WebSocket client disconnected")
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        active_connections.discard(websocket)
        logger.info("WebSocket client disconnected cleanly")
    except Exception as e:
        logger.exception("Unhandled error in WebSocket feed loop")


# Admin: Set webhook URL (persisting in-memory or patch later to env/db)
@router.post("/notifications/discord", status_code=204)
async def save_webhook(payload: Dict[str, str], user=Depends(get_current_admin_user)):
    url = payload.get("webhook_url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing webhook_url")

    global DISCORD_WEBHOOK_URL
    DISCORD_WEBHOOK_URL = url
    logger.info(f"[admin:{user.email}] saved Discord webhook: {url}")
    return Response(status_code=204)


# Admin: Post message as bot using webhook
@router.post("/notifications/discord/send")
async def post_discord_message(payload: Dict[str, str], user=Depends(get_current_admin_user)):
    message = payload.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Missing message")

    if not DISCORD_WEBHOOK_URL:
        raise HTTPException(status_code=500, detail="Webhook not configured")

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(DISCORD_WEBHOOK_URL, json={"content": message})
            res.raise_for_status()
            logger.info(f"[admin:{user.email}] sent message to Discord")
            return {"status": "ok"}
        except httpx.HTTPStatusError as e:
            logger.error(f"Webhook post error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=502, detail="Discord webhook error")
        except Exception as e:
            logger.exception("Failed to post Discord message")
            raise HTTPException(status_code=500, detail="Internal error")