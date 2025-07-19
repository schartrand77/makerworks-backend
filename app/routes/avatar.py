import io
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.config.settings import settings
from app.db.database import get_db
from app.dependencies.auth import get_user_from_headers
from app.models import User
from app.schemas.token import TokenData
from app.schemas.user import AvatarUploadResponse
from app.utils.users import create_user_dirs

router = APIRouter()

BASE_UPLOAD_DIR: Path = Path(settings.upload_dir)
BASE_URL: str = getattr(settings, "base_url", "http://localhost:8000").rstrip("/")
MAX_AVATAR_SIZE = (512, 512)
THUMB_SIZE = (128, 128)
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

ALLOWED_IMAGE_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}


def get_avatar_dir(user_id: str) -> Path:
    path = BASE_UPLOAD_DIR / "users" / user_id / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.post("/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    token: TokenData = Depends(get_user_from_headers),
    db: Session = Depends(get_db),
):
    user_id = token.sub

    # Validate MIME type
    content_type = file.content_type
    if content_type not in ALLOWED_IMAGE_MIME:
        raise HTTPException(400, detail=f"Unsupported image type: {content_type}")

    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
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

    try:
        image = Image.open(io.BytesIO(contents))
        image = image.convert("RGB")
        image.thumbnail(MAX_AVATAR_SIZE)

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=ext, dir=avatar_dir
        ) as tmp:
            image.save(tmp.name, optimize=True, quality=85)
            Path(tmp.name).replace(save_path)

        thumb = image.copy()
        thumb.thumbnail(THUMB_SIZE)
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=ext, dir=avatar_dir
        ) as tmp_thumb:
            thumb.save(tmp_thumb.name, optimize=True, quality=85)
            Path(tmp_thumb.name).replace(thumb_path)

    except Exception as e:
        logging.error(f"[AVATAR] Failed to process image: {e}")
        raise HTTPException(500, detail="Failed to process avatar image") from e

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if user.avatar_url:
        try:
            old_file = avatar_dir / Path(user.avatar_url).name
            old_thumb = old_file.with_name(f"{old_file.stem}_thumb{old_file.suffix}")
            for f in [old_file, old_thumb]:
                if f.exists():
                    f.unlink()
        except Exception as e:
            logging.warning(f"[AVATAR] Failed to delete old avatar: {e}")

    user.avatar_url = f"/uploads/users/{user_id}/avatars/{avatar_filename}"
    user.avatar_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    ts = int(user.avatar_updated_at.timestamp())

    return AvatarUploadResponse(
        status="ok",
        avatar_url=f"{BASE_URL}{user.avatar_url}?t={ts}",
        thumbnail_url=f"{BASE_URL}/uploads/users/{user_id}/avatars/{thumb_filename}?t={ts}",
        uploaded_at=user.avatar_updated_at,
    )


@router.get("/avatar/{user_id}")
async def get_avatar_url(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.avatar_url:
        raise HTTPException(404, detail="Avatar not found")

    ts = int(user.avatar_updated_at.timestamp()) if user.avatar_updated_at else 0
    thumb_url = user.avatar_url.replace(".", "_thumb.")

    return JSONResponse(
        {
            "avatar_url": f"{BASE_URL}{user.avatar_url}?t={ts}",
            "thumbnail_url": f"{BASE_URL}{thumb_url}?t={ts}",
        }
    )
