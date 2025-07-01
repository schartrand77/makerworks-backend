from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import ModelMetadata, User
from app.schemas.models import ModelUploadResponse
from app.schemas.token import TokenData
from app.dependencies.auth import get_user_from_headers
from app.config.settings import settings  # ✅ CORRECT
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import shutil
import logging
import os

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────
BASE_URL: str = getattr(settings, "base_url", "http://localhost:8000").rstrip("/")
AVATAR_DIR: Path = settings.avatar_dir
MODEL_DIR: Path = settings.model_dir

ALLOWED_MODEL_TYPES = [
    "application/octet-stream",
    "application/vnd.ms-pki.stl",
    "model/stl",
    "application/3mf",
]

ALLOWED_IMAGE_TYPES = [
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
]

# ─────────────────────────────────────────────────────────────
# Ensure upload directories exist
# ─────────────────────────────────────────────────────────────
def safe_mkdir(path):
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] Could not create directory {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Upload directory error: {e}")

safe_mkdir(AVATAR_DIR)
safe_mkdir(MODEL_DIR)

# ─────────────────────────────────────────────────────────────
# POST /api/v1/upload
# ─────────────────────────────────────────────────────────────
@router.post("/", response_model=ModelUploadResponse)
async def upload_model_or_avatar(
    file: UploadFile = File(...),
    type: str = Form(...),  # "model" or "avatar"
    name: str = Form(None),
    description: str = Form(""),
    token: TokenData = Depends(get_user_from_headers),
    db: Session = Depends(get_db),
):
    user_id = token.sub

    if type not in ["model", "avatar"]:
        logging.warning(f"[WARN] Invalid upload type: {type}")
        raise HTTPException(status_code=400, detail="Invalid upload type. Must be 'model' or 'avatar'.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if not ext:
        raise HTTPException(status_code=400, detail="Missing file extension.")

    # ─────────────── Upload Model ───────────────
    if type == "model":
        if file.content_type not in ALLOWED_MODEL_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported 3D model file type")

        model_id = str(uuid4())
        save_path = MODEL_DIR / f"{model_id}{ext}"
        logging.info(f"[MODEL] Saving model for user {user_id} to: {save_path}")

        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logging.error(f"[ERROR] Saving model failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to save model file")

        model = Model3D(
            id=model_id,
            name=name or file.filename,
            description=description,
            filename=file.filename,
            path=str(save_path),
            uploader_id=user_id,
            uploaded_at=datetime.utcnow(),
            geometry_hash=None,
            is_duplicate=False,
        )
        db.add(model)
        db.commit()
        db.refresh(model)

        return ModelUploadResponse(
            id=model.id,
            name=model.name,
            url=f"{BASE_URL}/uploads/stls/{model_id}{ext}",
            uploaded_at=model.uploaded_at.isoformat(),
        )

    # ─────────────── Upload Avatar ───────────────
    elif type == "avatar":
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported image type for avatar upload")

        avatar_id = f"{user_id}_{uuid4().hex[:8]}"
        save_path = AVATAR_DIR / f"{avatar_id}{ext}"
        logging.info(f"[AVATAR] Saving avatar for user {user_id} to: {save_path}")

        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logging.error(f"[ERROR] Saving avatar failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to save avatar file")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logging.warning(f"[WARN] No user found with ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        user.avatar_url = f"/uploads/avatars/{avatar_id}{ext}"
        db.commit()
        db.refresh(user)

        return ModelUploadResponse(
            id=avatar_id,
            name=file.filename,
            url=f"{BASE_URL}/uploads/avatars/{avatar_id}{ext}",
            uploaded_at=datetime.utcnow().isoformat(),
        )