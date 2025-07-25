# app/routes/avatar.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from datetime import datetime
import io
import subprocess
import os
import logging

from app.db.database import get_async_db
from app.models.models import User
from app.schemas.user import AvatarUploadResponse
from app.dependencies.auth import get_current_user
from app.config.settings import settings

router = APIRouter(prefix="/api/v1/avatar")
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB
MAX_AVATAR_SIZE = (256, 256)
THUMB_SIZE = (64, 64)

# ✅ Always use the absolute uploads path configured in settings
BASE_UPLOAD_DIR = Path(settings.uploads_path).resolve()

def get_avatar_dir(user_id: str) -> Path:
    avatar_dir = BASE_UPLOAD_DIR / "users" / user_id / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)

    # 🔒 Permission check
    if not os.access(avatar_dir, os.W_OK):
        logger.error(f"[AVATAR] No write permission for {avatar_dir.resolve()}")
        raise HTTPException(500, detail="Uploads folder is not writable")

    return avatar_dir

@router.post("", response_model=AvatarUploadResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    user_id = str(user.id)
    logger.info(f"[AVATAR] Upload initiated for user {user_id}")

    contents = await file.read()
    ext = ALLOWED_IMAGE_MIME.get(file.content_type)
    if not ext:
        raise HTTPException(400, detail="Unsupported image type")

    avatar_dir = get_avatar_dir(user_id)
    save_path = avatar_dir / f"avatar{ext}"
    thumb_path = avatar_dir / f"avatar_thumb{ext}"

    # ✅ Always write the uploaded file, even if Blender fails
    tmp_input = avatar_dir / f"input{ext}"
    tmp_input.write_bytes(contents)

    try:
        try:
            render_with_blender(tmp_input, save_path, thumb_path, use_gpu=False)
            tmp_input.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"[AVATAR] Blender failed: {e} → using Pillow fallback")
            from PIL import Image
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            image.thumbnail(MAX_AVATAR_SIZE)
            image.save(save_path, optimize=True, quality=85)

            thumb = image.copy()
            thumb.thumbnail(THUMB_SIZE)
            thumb.save(thumb_path, optimize=True, quality=85)

    except Exception as e:
        logger.error(f"[AVATAR] Fatal error saving avatar: {e}")
        raise HTTPException(500, detail="Failed to save avatar")

    # ✅ Validate file existence before committing
    if not save_path.exists():
        logger.error(f"[AVATAR] File was NOT written: {save_path.resolve()}")
        raise HTTPException(500, detail="Avatar file was not created")

    logger.info(f"[AVATAR] Saved avatar to: {save_path.resolve()}")

    # DB update stays the same
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    user.avatar_url = f"/uploads/users/{user_id}/avatars/{save_path.name}"
    user.avatar_updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    ts = int(user.avatar_updated_at.timestamp())

    return AvatarUploadResponse(
        status="ok",
        avatar_url=f"{settings.base_url}{user.avatar_url}?t={ts}",
        thumbnail_url=f"{settings.base_url}/uploads/users/{user_id}/avatars/{thumb_path.name}?t={ts}",
        uploaded_at=user.avatar_updated_at,
    )
