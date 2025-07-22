# app/routes/admin.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_async_db
from app.dependencies.auth import admin_required
from app.models.models import ModelMetadata, User
from app.services.auth_service import log_action
from app.utils.logging import logger

router = APIRouter()

# In-memory temporary config store
discord_config = {
    "webhook_url": "",
    "channel_id": "",
    "feed_enabled": True,
}


@router.get("/users")
async def get_all_users(db: AsyncSession = Depends(get_async_db), admin=Depends(admin_required)):
    """
    List all users.
    """
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


@router.post("/users/{user_id}/promote")
async def promote_user(
    user_id: str, db: AsyncSession = Depends(get_async_db), admin=Depends(admin_required)
):
    """
    Promote a user to admin role.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = "admin"
    await log_action(admin.sub, "promote_user", user_id, db)
    await db.commit()
    return {"status": "ok", "message": f"User {user_id} promoted to admin."}


@router.post("/users/{user_id}/demote")
async def demote_user(
    user_id: str, db: AsyncSession = Depends(get_async_db), admin=Depends(admin_required)
):
    """
    Demote an admin user back to regular user.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = "user"
    await log_action(admin.sub, "demote_user", user_id, db)
    await db.commit()
    return {"status": "ok", "message": f"User {user_id} demoted to user."}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str, db: AsyncSession = Depends(get_async_db), admin=Depends(admin_required)
):
    """
    Delete a user account.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await log_action(admin.sub, "delete_user", user_id, db)
    await db.commit()
    return {"status": "ok", "message": f"User {user_id} deleted."}


@router.post("/users/{user_id}/reset-password")
async def force_password_reset(
    user_id: str, db: AsyncSession = Depends(get_async_db), admin=Depends(admin_required)
):
    """
    Log a password reset event. Actual reset flow depends on frontend.
    """
    await log_action(admin.sub, "force_password_reset", user_id, db)
    return {
        "status": "noop",
        "message": "Password reset flow to be handled by frontend."
    }


@router.get("/users/{user_id}/uploads")
async def view_user_uploads(
    user_id: str, db: AsyncSession = Depends(get_async_db), admin=Depends(admin_required)
):
    """
    View all uploads belonging to a specific user.
    """
    result = await db.execute(
        select(ModelMetadata).where(ModelMetadata.user_id == user_id)
    )
    uploads = result.scalars().all()
    return uploads


@router.get("/discord/config")
async def get_discord_config(admin=Depends(admin_required)):
    """
    Get the current Discord webhook/channel config.
    """
    return discord_config


@router.post("/discord/config")
async def update_discord_config(
    request: Request,
    admin=Depends(admin_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update the Discord webhook/channel config.
    """
    data = await request.json()
    discord_config.update(
        {
            "webhook_url": data.get("webhook_url", discord_config["webhook_url"]),
            "channel_id": data.get("channel_id", discord_config["channel_id"]),
            "feed_enabled": data.get("feed_enabled", discord_config["feed_enabled"]),
        }
    )
    await log_action(admin.sub, "update_discord_config", admin.sub, db)
    return {"status": "ok", "message": "Discord configuration updated."}


@router.post("/unlock")
async def god_mode_unlock(request: Request, admin=Depends(admin_required)):
    """
    Hidden route for Konami Code God Mode.
    """
    client_ip = request.client.host
    logger.warning(f"👑 God Mode unlock triggered from {client_ip}")
    return {"status": "ok", "message": f"God Mode unlocked from {client_ip}"}
