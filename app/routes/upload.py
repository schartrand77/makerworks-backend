# app/routes/upload.py

import os
import json
import subprocess

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ModelMetadata
from app.utils.storage import (
    save_upload_to_disk,
    move_file,
    get_storage_paths,
    generate_unique_filename,
    is_valid_model_file,
)
from app.utils.validation import validate_file_size

# from app.routes.auth import get_current_user
# from app.schemas import User  # Optional: enable for uploader auth

BLENDER_PATH = "/usr/bin/blender"  # Update if needed

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/model")
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(...),
    tags: str = Form(""),
    category: str = Form("uncategorized"),
    role: str = Form("user"),
    db: AsyncSession = Depends(get_db),
    # user: User = Depends(get_current_user)  # Optional: secure upload
):
    if not is_valid_model_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    unique_name = generate_unique_filename(file.filename)
    tmp_path, final_path = get_storage_paths("/app/uploads", unique_name)
    json_out = tmp_path + ".json"
    preview_out = final_path.replace("/models/", "/previews/") + ".png"

    await save_upload_to_disk(file, tmp_path)

    try:
        validate_file_size(tmp_path)
    except ValueError as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=413, detail=str(e))

    try:
        subprocess.run(
            [BLENDER_PATH, "-b", "-P", "scripts/extract_metadata.py", "--", tmp_path, json_out, preview_out],
            check=True
        )
    except subprocess.CalledProcessError as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=500, detail="Failed to extract metadata from model")

    if not os.path.exists(json_out):
        os.remove(tmp_path)
        raise HTTPException(status_code=500, detail="Metadata extraction output missing")

    with open(json_out, "r") as f:
        try:
            metadata = json.load(f)
        except json.JSONDecodeError:
            os.remove(tmp_path)
            raise HTTPException(status_code=500, detail="Invalid metadata output format")

    move_file(tmp_path, final_path)

    model = ModelMetadata(
        filename=unique_name,
        filepath=final_path,
        preview_image=preview_out,
        uploader="user123",  # Replace with `user.id` if auth is enabled
        role=role,
        name=name,
        description=description,
        tags=tags,
        category=category,
        volume_mm3=metadata.get("volume_mm3", 0),
        dimensions_mm=metadata.get("dimensions_mm", {}),
        face_count=metadata.get("face_count", 0),
    )

    db.add(model)
    await db.commit()
    await db.refresh(model)

    return {
        "status": "success",
        "model_id": model.id,
        "preview": preview_out,
        "name": model.name,
    }