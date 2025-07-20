# app/routes/avatar.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import io
import tempfile
import subprocess
import os
import logging

from app.db.database import get_db
from app.models.models import User
from app.schemas.user import AvatarUploadResponse
from app.dependencies.auth import get_user_from_headers
from app.config.settings import settings

router = APIRouter(tags=["Users"])
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


def has_gpu() -> bool:
    """
    Check if the system has a GPU that Blender can use.
    """
    try:
        result = subprocess.run(
            [
                "blender", "--background", "--factory-startup", "--python-expr",
                "import bpy; "
                "prefs=bpy.context.preferences.addons['cycles'].preferences; "
                "prefs.compute_device_type='CUDA'; "
                "devices=prefs.devices; "
                "print(any(d.use for d in devices))"
            ],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            logger.warning(f"[AVATAR] GPU check failed: {result.stderr}")
            return False
        return "True" in result.stdout
    except Exception as e:
        logger.warning(f"[AVATAR] GPU check exception: {e}")
        return False


def render_with_blender(input_path: Path, output_path: Path, thumb_path: Path, use_gpu: bool):
    """
    Run Blender script to process avatar with optional GPU acceleration.
    """
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


@router.post("/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db),
):
    user_id = str(user.id)

    logger.info(f"[AVATAR] Upload initiated for user {user_id}")

    content_type = file.content_type
    if content_type not in ALLOWED_IMAGE_MIME:
        logger.warning(f"[AVATAR] Unsupported content type: {content_type}")
        raise HTTPException(400, detail=f"Unsupported image type: {content_type}")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        logger.warning(f"[AVATAR] File too large: {len(contents)} bytes")
        raise HTTPException(
            400,
            detail=f"Avatar file too large (max {MAX_FILE_SIZE_BYTES//1024//1024} MB)",
        )

    ext = ALLOWED_IMAGE_MIME[content_type]
    avatar_uuid = uuid4().hex
    base_name = f"{user_id}_{avatar_uuid}"
    avatar_filename = f"{base_name}{ext}"
    thumb_filename = f"{base_name}_thumb{ext}"
    avatar_dir = get_avatar_dir(user_id)
    save_path = avatar_dir / avatar_filename
    thumb_path = avatar_dir / thumb_filename

    tmp_input = avatar_dir / f"{base_name}_input{ext}"
    tmp_input.write_bytes(contents)

    try:
        gpu_available = has_gpu()
        render_with_blender(tmp_input, save_path, thumb_path, gpu_available)
        tmp_input.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"[AVATAR] Blender failed, falling back to Pillow: {e}")
        from PIL import Image

        try:
            image = Image.open(io.BytesIO(contents))
            image = image.convert("RGB")
            image.thumbnail(MAX_AVATAR_SIZE)

            with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=avatar_dir) as tmp:
                image.save(tmp.name, optimize=True, quality=85)
                Path(tmp.name).replace(save_path)

            thumb = image.copy()
            thumb.thumbnail(THUMB_SIZE)
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=avatar_dir) as tmp_thumb:
                thumb.save(tmp_thumb.name, optimize=True, quality=85)
                Path(tmp_thumb.name).replace(thumb_path)

        except Exception as e:
            logger.error(f"[AVATAR] Failed to process image for user {user_id}: {e}")
            raise HTTPException(500, detail="Failed to process avatar image") from e

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.error(f"[AVATAR] User {user_id} not found in DB after upload")
        raise HTTPException(404, "User not found")

    if user.avatar_url:
        try:
            old_file = avatar_dir / Path(user.avatar_url).name
            old_thumb = old_file.with_name(f"{old_file.stem}_thumb{old_file.suffix}")
            for f in [old_file, old_thumb]:
                if f.exists():
                    f.unlink()
                    logger.info(f"[AVATAR] Deleted old avatar file: {f}")
        except Exception as e:
            logger.warning(f"[AVATAR] Failed to delete old avatar: {e}")

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


@router.get("/avatar/{user_id}")
async def get_avatar_url(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.avatar_url:
        logger.warning(f"[AVATAR] Avatar not found for user {user_id}")
        raise HTTPException(404, detail="Avatar not found")

    ts = int(user.avatar_updated_at.timestamp()) if user.avatar_updated_at else 0
    thumb_url = user.avatar_url.replace(".", "_thumb.")

    logger.info(f"[AVATAR] Retrieved avatar URLs for user {user_id}")

    return JSONResponse(
        {
            "avatar_url": f"{settings.base_url}{user.avatar_url}?t={ts}",
            "thumbnail_url": f"{settings.base_url}{thumb_url}?t={ts}",
        }
    )
