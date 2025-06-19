from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Model3D
from app.schemas.models import ModelUploadResponse
#from app.utils.hash_geometry import generate_geometry_hash  # if used
from uuid import uuid4
from datetime import datetime
import os
import shutil

router = APIRouter()

UPLOAD_DIR = "/app/uploads"

@router.post("/", response_model=ModelUploadResponse)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    if file.content_type not in ["application/octet-stream", "application/vnd.ms-pki.stl", "model/stl", "application/3mf"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    ext = os.path.splitext(file.filename)[1]
    model_id = str(uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{model_id}{ext}")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Optional: compute hash to detect duplicates
    geometry_hash = generate_geometry_hash(save_path)

    # Optional: check if already exists
    existing = db.query(Model3D).filter_by(geometry_hash=geometry_hash).first()
    if existing:
        raise HTTPException(status_code=409, detail="Duplicate model detected")

    # Create DB entry
    model = Model3D(
        id=model_id,
        name=name,
        description=description,
        filename=file.filename,
        path=save_path,
        uploader_id=user_id,
        uploaded_at=datetime.utcnow(),
        geometry_hash=geometry_hash,
        is_duplicate=False,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    # Optional: Queue preview job via Celery
    # queue_thumbnail_job.delay(model_id)

    return ModelUploadResponse(
        id=model.id,
        name=model.name,
        url=f"/static/uploads/{model_id}{ext}",
        uploaded_at=model.uploaded_at.isoformat()
    )