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
from app.dependencies.auth import get_current_user
from app.models import ModelMetadata as Model3D, User
from app.schemas.models import ModelUploadResponse

router = APIRouter(redirect_slashes=False)
logger = logging.getLogger(__name__)

BASE_URL: str = getattr(settings, "base_url", "http://localhost:8000").rstrip("/")
BASE_UPLOAD_DIR: Path = (Path(__file__).resolve().parent.parent / settings.uploads_path).resolve()
logger.info(f"[UPLOAD] Base upload dir resolved: {BASE_UPLOAD_DIR}")

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {".stl", ".3mf"}
ALLOWED_MODEL_TYPES = {
    "application/octet-stream",
    "application/vnd.ms-pki.stl",
    "model/stl",
    "application/3mf",
}

BLENDER_SCRIPT = (Path(__file__).parent.parent / "scripts" / "blender_pipeline.py").resolve()


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


def run_blender_pipeline(model_path: Path, output_dir: Path) -> dict:
    if not BLENDER_SCRIPT.exists():
        logger.error("[UPLOAD] Blender pipeline script missing.")
        raise HTTPException(500, "Blender pipeline script missing.")

    cmd = [
        "blender",
        "--background",
        "--factory-startup",
        "--python-expr",
        # Ensure STL addon is enabled before running pipeline
        "import bpy; bpy.ops.wm.addon_enable(module='io_mesh_stl')",
        "--python", str(BLENDER_SCRIPT),
        "--", str(model_path), str(output_dir)
    ]
    logger.info(f"[UPLOAD] Running Blender pipeline: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as e:
        logger.exception(f"[UPLOAD] Failed to execute Blender pipeline: {e}")
        raise HTTPException(500, "Failed to execute Blender pipeline.") from e

    if result.returncode != 0:
        logger.error(f"[UPLOAD] Blender pipeline failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        if "import_mesh.stl" in result.stdout or "import_mesh.stl" in result.stderr:
            raise HTTPException(500, "Blender STL import add-on is missing or failed to load.")
        raise HTTPException(500, "Blender pipeline failed.")

    stdout_clean = result.stdout.strip()
    if not stdout_clean:
        logger.error(f"[UPLOAD] Blender pipeline returned empty output.\nSTDERR:\n{result.stderr}")
        raise HTTPException(500, "Blender pipeline returned empty output.")

    try:
        data = json.loads(stdout_clean)
        logger.debug(f"[UPLOAD] Blender pipeline output parsed successfully.")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"[UPLOAD] Invalid JSON from Blender pipeline.\nSTDOUT:\n{stdout_clean}\nSTDERR:\n{result.stderr}")
        raise HTTPException(500, "Invalid JSON from Blender pipeline.") from e


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
        raise HTTPException(400, f"Invalid file extension: {ext}. Only .stl and .3mf are allowed.")

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

    blender_output = run_blender_pipeline(save_path, model_dir)

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
