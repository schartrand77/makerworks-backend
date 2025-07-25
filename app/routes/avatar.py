import os
import shutil
import subprocess
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

    # Decide processing based on extension
    if ext in UPLOAD_EXTENSIONS_3D:
        # 3D file → run Blender render
        script_path = os.path.join(settings.BASE_DIR, "scripts", "render_avatar.py")
        process = subprocess.run(
            [
                settings.BLENDER_PATH,
                "--background",
                "--python", script_path,
                "--",
                input_path,
                user_dir
            ],
            capture_output=True,
            text=True
        )

        if process.returncode != 0:
            raise HTTPException(status_code=500, detail="Blender render failed")
    else:
        # 2D image → Pillow resize/crop, skip Blender
        avatar_path = os.path.join(user_dir, "avatar.png")
        try:
            with Image.open(input_path) as img:
                img = img.convert("RGBA")
                img.thumbnail((512, 512))
                img.save(avatar_path, "PNG")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image processing failed: {e}")
        finally:
            os.remove(input_path)

    # Update DB with new avatar timestamp
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(avatar_updated_at=datetime.utcnow())
    )
    await db.commit()

    return {"status": "ok", "avatar_url": f"/uploads/users/{user_id}/avatars/avatar.png"}
