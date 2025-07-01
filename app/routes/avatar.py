from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from app.db.database import get_db
from app.models import User
from app.dependencies.auth import get_user_from_headers
from app.schemas.token import TokenData
from app.config.settings import settings
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from PIL import Image
import shutil
import logging
import os
import magic  # requires: pip install python-magic

router = APIRouter()
AVATAR_DIR: Path = Path(settings.avatar_dir)
BASE_URL: str = getattr(settings, "base_url", "http://localhost:8000").rstrip("/")
MAX_AVATAR_SIZE = (512, 512)
THUMB_SIZE = (128, 128)

# ─────────────────────────────────────────────────────────────
# Init
# ─────────────────────────────────────────────────────────────
def safe_mkdir(path: Path):
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"[AVATAR] Could not create avatar dir {path}: {e}")
        raise HTTPException(500, f"Avatar storage error: {e}")

safe_mkdir(AVATAR_DIR)

ALLOWED_IMAGE_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}

# ─────────────────────────────────────────────────────────────
# POST /users/avatar
# ─────────────────────────────────────────────────────────────
@router.post("/users/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    token: TokenData = Depends(get_user_from_headers),
    db: Session = Depends(get_db),
):
    user_id = token.sub

    # Validate MIME type
    content_type = file.content_type
    if content_type not in ALLOWED_IMAGE_MIME:
        raise HTTPException(400, detail="Unsupported avatar image type")

    ext = ALLOWED_IMAGE_MIME[content_type]
    avatar_uuid = uuid4().hex
    avatar_filename = f"{user_id}_{avatar_uuid}{ext}"
    thumb_filename = f"{user_id}_{avatar_uuid}_thumb{ext}"
    save_path = AVATAR_DIR / avatar_filename
    thumb_path = AVATAR_DIR / thumb_filename

    # Open and resize image
    try:
        image = Image.open(file.file)
        image = image.convert("RGB")

        # Save full-size avatar
        image.thumbnail(MAX_AVATAR_SIZE)
        image.save(save_path)

        # Save thumbnail
        thumb = image.copy()
        thumb.thumbnail(THUMB_SIZE)
        thumb.save(thumb_path)

    except Exception as e:
        logging.error(f"[AVATAR] Failed to process image: {e}")
        raise HTTPException(500, detail="Failed to process avatar image")

    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    # Delete previous avatar + thumbnail
    if user.avatar_url:
        try:
            old_file = Path(settings.avatar_dir) / Path(user.avatar_url).name
            old_thumb = old_file.parent / f"{old_file.stem}_thumb{old_file.suffix}"
            for f in [old_file, old_thumb]:
                if f.exists():
                    f.unlink()
        except Exception as e:
            logging.warning(f"[AVATAR] Failed to delete old avatar: {e}")

    # Save new URLs
    user.avatar_url = f"/uploads/avatars/{avatar_filename}"
    user.avatar_updated_at = datetime.utcnow()
    db.commit()

    return JSONResponse(
        {
            "status": "ok",
            "avatar_url": f"{BASE_URL}{user.avatar_url}?t={int(user.avatar_updated_at.timestamp())}",
            "thumbnail_url": f"{BASE_URL}/uploads/avatars/{thumb_filename}?t={int(user.avatar_updated_at.timestamp())}",
            "uploaded_at": user.avatar_updated_at.isoformat(),
        }
    )

# ─────────────────────────────────────────────────────────────
# GET /users/avatar/{user_id}
# ─────────────────────────────────────────────────────────────
@router.get("/users/avatar/{user_id}")
async def get_avatar_url(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.avatar_url:
        raise HTTPException(404, detail="Avatar not found")

    thumb_url = user.avatar_url.replace(".", "_thumb.")
    return JSONResponse(
        {
            "avatar_url": f"{BASE_URL}{user.avatar_url}?t={int(user.avatar_updated_at.timestamp())}",
            "thumbnail_url": f"{BASE_URL}{thumb_url}?t={int(user.avatar_updated_at.timestamp())}"
        }
    )