import logging
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import trimesh

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.database import get_async_db
from app.dependencies.auth import get_current_user
from app.models import ModelMetadata as Model3D, User
from app.schemas.models import ModelUploadResponse

router = APIRouter(redirect_slashes=False)
logger = logging.getLogger(__name__)

BASE_URL: str = getattr(settings, "base_url", "http://localhost:8000").rstrip("/")
BASE_UPLOAD_DIR: Path = (Path(__file__).resolve().parent.parent / settings.uploads_path).resolve()
logger.info(f"[UPLOAD] Base upload dir resolved: {BASE_UPLOAD_DIR}")

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {".stl"}
ALLOWED_MODEL_TYPES = {
    "application/octet-stream",
    "application/vnd.ms-pki.stl",
    "model/stl",
}


def get_model_dir(user_id: str) -> Path:
    """
    Safely creates and returns the model directory for a user.
    """
    safe_user_id = str(user_id).strip()
    path = (BASE_UPLOAD_DIR / "users" / safe_user_id / "models").resolve()
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"[UPLOAD] Model dir for user {safe_user_id}: {path}")
    return path


def save_file(destination: Path, data: bytes):
    try:
        with open(destination, "wb") as buffer:
            buffer.write(data)
    except Exception as e:
        logger.exception(f"[UPLOAD] Saving file failed: {e}")
        raise HTTPException(500, "Failed to save file") from e


def validate_file_size(data: bytes, max_size: int):
    if len(data) > max_size:
        raise HTTPException(400, f"File too large (max {max_size // (1024*1024)} MB)")


def process_model_file(model_path: Path, output_dir: Path) -> dict:
    """Generate metadata and a thumbnail for the uploaded model."""
    try:
        mesh = trimesh.load(str(model_path), force="mesh")
    except Exception as e:
        logger.exception(f"[UPLOAD] Failed to load model: {e}")
        raise HTTPException(400, "Invalid 3D model") from e

    metadata = {
        "volume": float(mesh.volume) if mesh.is_volume else None,
        "bbox": mesh.bounding_box.extents.tolist(),
        "faces": int(len(mesh.faces)),
        "vertices": int(len(mesh.vertices)),
    }

    thumb_rel = None
    try:
        scene = mesh.scene()
        png = scene.save_image(resolution=(512, 512), visible=False)
        if png:
            thumb_path = output_dir / f"{model_path.stem}_thumbnail.png"
            with open(thumb_path, "wb") as f:
                f.write(png)
            thumb_rel = str(thumb_path.relative_to(BASE_UPLOAD_DIR))
    except Exception as e:
        logger.exception(f"[UPLOAD] Thumbnail generation failed: {e}")

    return {"metadata": metadata, "thumbnail": thumb_rel}


@router.post("", response_model=ModelUploadResponse)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(None),
    description: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    user_id = str(user.id)

    if not file.filename:
        raise HTTPException(400, "No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if not ext:
        raise HTTPException(400, "Missing file extension.")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Invalid file extension: {ext}. Only .stl is allowed.")

    contents = await file.read()
    validate_file_size(contents, MAX_FILE_SIZE_BYTES)

    if file.content_type not in ALLOWED_MODEL_TYPES:
        logger.warning(f"[UPLOAD] Unusual content type '{file.content_type}' for file '{file.filename}'")

    now = datetime.utcnow()
    now_iso = now.isoformat()

    model_id = str(uuid4())
    model_dir = get_model_dir(user_id)
    save_path = (model_dir / f"{model_id}{ext}").resolve()
    logger.info(f"[UPLOAD] Saving model for user {user_id} to: {save_path}")

    save_file(save_path, contents)

    result = process_model_file(save_path, model_dir)

    metadata = result.get("metadata", {})
    thumbnail_rel_path = result.get("thumbnail")

    model_kwargs = {
        "id": model_id,
        "name": name or file.filename,
        "description": description,
        "filename": file.filename,
        "filepath": str(save_path.relative_to(BASE_UPLOAD_DIR)),
        "uploader_id": user_id,
        "uploaded_at": now,
        "geometry_hash": None,
        "is_duplicate": False,
        "volume": metadata.get("volume"),
        "bbox": json.dumps(metadata.get("bbox", [])),
        "faces": metadata.get("faces", 0),
        "vertices": metadata.get("vertices", 0),
        "thumbnail_url": f"{BASE_URL}/uploads/{thumbnail_rel_path}" if thumbnail_rel_path else None,
    }

    model = Model3D(**model_kwargs)
    db.add(model)
    await db.commit()
    await db.refresh(model)

    logger.info(f"[UPLOAD] Model {model.id} uploaded & processed for user {user_id}")

    return ModelUploadResponse(
        id=model.id,
        name=model.name,
        url=f"{BASE_URL}/uploads/users/{user_id}/models/{model_id}{ext}",
        uploaded_at=now_iso,
        thumbnail_url=f"{BASE_URL}/uploads/{thumbnail_rel_path}" if thumbnail_rel_path else None,
    )
