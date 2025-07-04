from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import httpx
import os

from app.models import ModelMetadata, Model3D
from app.db.database import get_db
from app.dependencies.auth import admin_required  # ✅ Ensure proper path
from app.services.auth_service import log_action

router = APIRouter(prefix="/admin", tags=["admin"])

AUTHENTIK_API = os.getenv("AUTHENTIK_API_URL", "http://authentik:9000")
AUTHENTIK_TOKEN = os.getenv("AUTHENTIK_API_TOKEN", "")

# In-memory temporary config store (replace with Redis or DB later)
discord_config = {
    "webhook_url": os.getenv("DISCORD_WEBHOOK_URL", ""),
    "channel_id": os.getenv("DISCORD_CHANNEL_ID", ""),
    "feed_enabled": True,
}


@router.get("/users")
async def get_all_users(admin=Depends(admin_required)):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                f"{AUTHENTIK_API}/api/v3/core/users/",
                headers={"Authorization": f"Bearer {AUTHENTIK_TOKEN}"}
            )
            res.raise_for_status()
            return res.json()
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Unable to reach Authentik")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch users from Authentik")


@router.post("/users/{user_id}/promote")
async def promote_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    await log_action(admin.sub, "promote_user", user_id, db)
    return {
        "status": "noop",
        "message": "Promotion should be done in Authentik Groups or Roles"
    }


@router.post("/users/{user_id}/demote")
async def demote_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    await log_action(admin.sub, "demote_user", user_id, db)
    return {
        "status": "noop",
        "message": "Demotion should be handled via Authentik roles"
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    await log_action(admin.sub, "delete_user", user_id, db)
    return {
        "status": "noop",
        "message": "Deletion must be performed via Authentik UI/API"
    }


@router.post("/users/{user_id}/reset-password")
async def force_password_reset(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    await log_action(admin.sub, "force_password_reset", user_id, db)
    return {
        "status": "noop",
        "message": "Password reset must be triggered in Authentik"
    }


@router.get("/users/{user_id}/uploads")
async def view_user_uploads(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    result = await db.execute(
        select(ModelMetadata)
        .join(Model3D, ModelMetadata.model_id == Model3D.id)
        .where(Model3D.uploader_id == user_id)
    )
    return result.scalars().all()


@router.get("/discord/config")
async def get_discord_config(admin=Depends(admin_required)):
    return discord_config


@router.post("/discord/config")
async def update_discord_config(
    request: Request,
    admin=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    data = await request.json()
    discord_config.update({
        "webhook_url": data.get("webhook_url", discord_config["webhook_url"]),
        "channel_id": data.get("channel_id", discord_config["channel_id"]),
        "feed_enabled": data.get("feed_enabled", discord_config["feed_enabled"]),
    })
    await log_action(admin.sub, "update_discord_config", admin.sub, db)
    return {"status": "ok", "message": "Discord configuration updated."}
