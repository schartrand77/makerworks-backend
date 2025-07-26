import os
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from PIL import Image

from app.db.session import get_db
from app.models.models import User
from app.dependencies.auth import get_current_user
from app.core.config import settings
from app.services.cache.user_cache import cache_user_profile, invalidate_user_cache  # ✅ Redis cache helpers
from app.schemas.users import UserOut  # ✅ Pydantic schema for serialization

router = APIRouter()

UPLOAD_EXTENSIONS_3D = {".stl", ".obj", ".blend"}

@router.post("/api/v1/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    user_dir = os.path.join(settings.UPLOAD_DIR, "users", str(user_id), "avatars")
    os.makedirs(user_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    input_path = os.path.join(user_dir, "input" + ext)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ Process avatar
    avatar_path = os.path.join(user_dir, "avatar.png")

    if ext in UPLOAD_EXTENSIONS_3D:
        script_path = os.path.join(Path(__file__).resolve().parents[2], "scripts", "render_avatar.py")
        process = subprocess.run(
            [sys.executable, script_path, input_path, user_dir],
            capture_output=True,
            text=True
        )

        if process.returncode != 0:
            raise HTTPException(status_code=500, detail="Avatar render failed")
    else:
        try:
            with Image.open(input_path) as img:
                img = img.convert("RGBA")
                img.thumbnail((512, 512))
                img.save(avatar_path, "PNG")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image processing failed: {e}")
        finally:
            os.remove(input_path)

    # ✅ Update DB timestamp
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(avatar_updated_at=datetime.utcnow())
    )
    await db.commit()

    # ✅ Convert ORM -> Pydantic before caching to avoid AttributeError
    pydantic_user = UserOut.model_validate(current_user)

    # ✅ Bust Redis cache and repopulate with fresh user profile
    await invalidate_user_cache(user_id, current_user.username)
    await cache_user_profile(pydantic_user)

    avatar_url = f"/uploads/users/{user_id}/avatars/avatar.png"

    return {
        "status": "ok",
        "avatar_url": avatar_url
    }
