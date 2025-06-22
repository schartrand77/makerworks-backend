from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models import ModelMetadata
from app.schemas.users import UserOut
from app.database import get_db
from app.dependencies import admin_required
from app.services.auth_service import log_action

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserOut])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.post("/users/{user_id}/promote")
async def promote_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = "admin"
    await db.commit()
    await log_action(admin.id, "promote", user_id, db)
    return {"status": "promoted"}


@router.post("/users/{user_id}/demote")
async def demote_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = "user"
    await db.commit()
    await log_action(admin.id, "demote", user_id, db)
    return {"status": "demoted"}


@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    await log_action(admin.id, "delete", user_id, db)
    return {"status": "deleted"}


@router.post("/users/{user_id}/reset-password")
async def force_password_reset(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Implement real password reset logic here
    await log_action(admin.id, "reset_password", user_id, db)
    return {"status": "reset_triggered"}


@router.get("/users/{user_id}/uploads")
async def view_user_uploads(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_required)
):
    result = await db.execute(select(ModelMetadata).where(ModelMetadata.user_id == user_id))
    uploads = result.scalars().all()
    return uploads