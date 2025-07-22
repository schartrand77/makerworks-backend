import logging
import subprocess
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.database import get_async_db
from app.dependencies.auth import get_user_from_headers
from app.models import ModelMetadata as Model3D, User
from app.schemas.models import ModelUploadResponse

router = APIRouter()
logger = logging.getLogger(__name__)

BASE_URL: str = getattr(settings, "base_url", "http://localhost:8000").rstrip("/")
BASE_UPLOAD_DIR: Path = Path(settings.upload_dir)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {".stl", ".3mf"}
ALLOWED_MODEL_TYPES = {
    "application/octet-stream",
    "application/vnd.ms-pki.stl",
    "model/stl",
    "application/3mf",
}

BLENDER_SCRIPT = Path(__file__).parent.parent / "scripts" / "blender_pipeline.py"


def get_model_dir(user_id: str) -> Path:
    path = BASE_UPLOAD_DIR / "users" / user_id / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_file(destination: Path, data: bytes):
    try:
        with open(destination, "wb") as buffer:
            buffer.write(data)
    except Exception as e:
        logger.exception(f"Saving file failed: {e}")
        raise HTTPException(500, "Failed to save file") from e


def validate_file_size(data: bytes, max_size: int):
    if len(data) > max_size:
        raise HTTPException(400, f"File too large (max {max_size // (1024*1024)} MB)")


def run_blender_pipeline(model_path: Path, output_dir: Path) -> dict:
    if not BLENDER_SCRIPT.exists():
        logger.error("Blender pipeline script missing.")
        raise HTTPException(500, "Blender pipeline script missing.")
    cmd = [
        "blender", "--background", "--python", str(BLENDER_SCRIPT.resolve()),
        "--", str(model_path.resolve()), str(output_dir.resolve())
    ]
    logger.info(f"Running Blender pipeline: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Blender pipeline failed. stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        raise HTTPException(500, "Blender pipeline failed.")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from Blender pipeline: {result.stdout}")
        raise HTTPException(500, "Invalid JSON from Blender pipeline.")


@router.post("/", response_model=ModelUploadResponse)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(None),
    description: str = Form(""),
    user: User = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_async_db),
):
    user_id = str(user.id)

    if not file.filename:
        raise HTTPException(400, "No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if not ext:
        raise HTTPException(400, "Missing file extension.")

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Invalid file extension: {ext}. Only .stl and .3mf are allowed.")

    contents = await file.read()
    validate_file_size(contents, MAX_FILE_SIZE_BYTES)

    if file.content_type not in ALLOWED_MODEL_TYPES:
        logger.warning(f"Unusual content type '{file.content_type}' for file '{file.filename}'")

    now = datetime.utcnow()
    now_iso = now.isoformat()

    model_id = str(uuid4())
    model_dir = get_model_dir(user_id)
    save_path = model_dir / f"{model_id}{ext}"
    logger.info(f"Saving model for user {user_id} to: {save_path}")

    save_file(save_path, contents)

    output_dir = model_dir
    blender_output = run_blender_pipeline(save_path, output_dir)

    metadata = blender_output.get("metadata", {})
    thumbnail_rel_path = blender_output.get("thumbnail")
    webm_rel_path = blender_output.get("webm")

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
        "thumbnail_url": f"{BASE_URL}/uploads/{thumbnail_rel_path}",
    }

    model = Model3D(**model_kwargs)

    db.add(model)
    await db.commit()
    await db.refresh(model)

    logger.info(f"Model {model.id} uploaded & processed for user {user_id}")

    return ModelUploadResponse(
        id=model.id,
        name=model.name,
        url=f"{BASE_URL}/uploads/users/{user_id}/models/{model_id}{ext}",
        uploaded_at=now_iso,
        thumbnail_url=f"{BASE_URL}/uploads/{thumbnail_rel_path}",
    )
