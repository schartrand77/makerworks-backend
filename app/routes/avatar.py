# app/routes/avatar.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
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


def get_avatar_dir(user_id: str) -> Path:
    base = Path("uploads") / "users" / user_id / "avatars"
    base.mkdir(parents=True, exist_ok=True)
    return base


def render_with_blender(input_path: Path, output_path: Path, thumb_path: Path, use_gpu: bool):
    env = os.environ.copy()
    env["USE_GPU"] = "1" if use_gpu else "0"
    cmd = [
        "blender",
        "--background",
        "--factory-startup",
        "--python",
        "scripts/render_avatar.py",
        "--",
        str(input_path),
        str(output_path),
        str(thumb_path),
    ]
    logger.info(f"[AVATAR] Running Blender for avatar render. GPU={use_gpu}")
    subprocess.run(cmd, env=env, check=True)


@router.post("", response_model=AvatarUploadResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    logger.debug(f"[AVATAR] Request headers: {dict(request.headers)}")
    user_id = str(user.id)
    logger.info(f"[AVATAR] Upload initiated for user {user_id}")

    if not user_id or user_id == "00000000-0000-0000-0000-000000000000":
        logger.error(f"[AVATAR] Invalid user_id={user_id}")
        raise HTTPException(401, detail="Invalid or missing user authentication")

    if file.content_type not in ALLOWED_IMAGE_MIME:
        logger.warning(f"[AVATAR] Unsupported content type: {file.content_type}")
        raise HTTPException(400, detail=f"Unsupported image type: {file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        logger.warning(f"[AVATAR] File too large: {len(contents)} bytes")
        raise HTTPException(
            400,
            detail=f"Avatar file too large (max {MAX_FILE_SIZE_BYTES//1024//1024} MB)",
        )

    ext = ALLOWED_IMAGE_MIME[file.content_type]
    avatar_filename = f"avatar{ext}"
    thumb_filename = f"avatar_thumb{ext}"
    avatar_dir = get_avatar_dir(user_id)
    save_path = avatar_dir / avatar_filename
    thumb_path = avatar_dir / thumb_filename

    for f in avatar_dir.glob("avatar*"):
        try:
            f.unlink()
            logger.info(f"[AVATAR] Deleted old avatar file: {f}")
        except Exception as e:
            logger.warning(f"[AVATAR] Failed to delete old avatar: {e}")

    tmp_input = avatar_dir / f"input{ext}"
    tmp_input.write_bytes(contents)

    try:
        use_gpu = False
        try:
            result = subprocess.run(
                [
                    "blender", "--background", "--factory-startup", "--python-expr",
                    "import bpy; prefs=bpy.context.preferences.addons['cycles'].preferences;"
                    "prefs.compute_device_type='CUDA'; devices=prefs.devices;"
                    "print(any(d.use for d in devices))"
                ],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and "True" in result.stdout:
                use_gpu = True
        except Exception as e:
            logger.warning(f"[AVATAR] GPU check failed: {e}")

        render_with_blender(tmp_input, save_path, thumb_path, use_gpu)
        tmp_input.unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"[AVATAR] Blender failed, falling back to Pillow: {e}")
        from PIL import Image

        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            image.thumbnail(MAX_AVATAR_SIZE)
            image.save(save_path, optimize=True, quality=85)

            thumb = image.copy()
            thumb.thumbnail(THUMB_SIZE)
            thumb.save(thumb_path, optimize=True, quality=85)
        except Exception as e:
            logger.error(f"[AVATAR] Failed to process image: {e}")
            raise HTTPException(500, detail="Failed to process avatar image") from e

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.error(f"[AVATAR] User {user_id} not found in DB after upload")
        raise HTTPException(404, "User not found")

    user.avatar_url = f"/uploads/users/{user_id}/avatars/{avatar_filename}"
    user.avatar_updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    ts = int(user.avatar_updated_at.timestamp())
    logger.info(f"[AVATAR] Upload complete for user {user_id}")

    return AvatarUploadResponse(
        status="ok",
        avatar_url=f"{settings.base_url}{user.avatar_url}?t={ts}",
        thumbnail_url=f"{settings.base_url}/uploads/users/{user_id}/avatars/{thumb_filename}?t={ts}",
        uploaded_at=user.avatar_updated_at,
    )
