import os
import json
import subprocess

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ModelMetadata
from app.schemas import ModelUploadRequest, ModelOut
from app.utils.auth import get_current_user, TokenData
from app.utils.storage import (
    save_upload_to_disk,
    move_file,
    get_storage_paths,
    generate_unique_filename,
    is_valid_model_file,
)
from app.utils.validation import validate_file_size

BLENDER_PATH = "/usr/bin/blender"  # Adjust as needed for Docker/host

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "/model",
    summary="Upload STL/3MF model and extract metadata",
    status_code=status.HTTP_201_CREATED,
)
async def upload_model(
    data: ModelUploadRequest = Depends(ModelUploadRequest.as_form),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Uploads a 3D model file and associated metadata. Extracts volume, dimensions, and preview using Blender.
    """

    if not is_valid_model_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    unique_name = generate_unique_filename(file.filename)
    tmp_path, final_path = get_storage_paths("/app/uploads", unique_name)
    json_out = tmp_path + ".json"
    preview_out = final_path.replace("/models/", "/previews/") + ".png"

    # Save uploaded file to disk
    await save_upload_to_disk(file, tmp_path)

    try:
        validate_file_size(tmp_path)
    except ValueError as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=413, detail=str(e))

    # Run Blender subprocess to extract metadata
    try:
        subprocess.run(
            [
                BLENDER_PATH,
                "-b",
                "-P",
                "scripts/extract_metadata.py",
                "--",
                tmp_path,
                json_out,
                preview_out,
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        os.remove(tmp_path)
        raise HTTPException(status_code=500, detail="Failed to extract metadata from model")

    if not os.path.exists(json_out):
        os.remove(tmp_path)
        raise HTTPException(status_code=500, detail="Metadata extraction output missing")

    # Parse metadata
    try:
        with open(json_out, "r") as f:
            metadata = json.load(f)
    except json.JSONDecodeError:
        os.remove(tmp_path)
        raise HTTPException(status_code=500, detail="Invalid metadata output format")

    # Move file to final location
    move_file(tmp_path, final_path)

    # Save model entry in DB
    model = ModelMetadata(
        filename=unique_name,
        filepath=final_path,
        preview_image=preview_out,
        uploader=str(user.sub),
        role=data.role,
        name=data.name,
        description=data.description,
        tags=",".join(data.tags),
        category=data.category,
        volume_mm3=metadata.get("volume_mm3", 0),
        dimensions_mm=metadata.get("dimensions_mm", {}),
        face_count=metadata.get("face_count", 0),
    )

    db.add(model)
    await db.commit()
    await db.refresh(model)

    return ModelOut.from_orm(model).serialize(role=user.role)