import logging
import subprocess
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.database import get_db
from app.dependencies.auth import get_user_from_headers
from app.models import ModelMetadata as Model3D, User
from app.schemas.models import ModelUploadResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────
BASE_URL: str = getattr(settings, "base_url", "http://localhost:8000").rstrip("/")
BASE_UPLOAD_DIR: Path = Path(settings.upload_dir)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_MODEL_TYPES = {
    "application/octet-stream",
    "application/vnd.ms-pki.stl",
    "model/stl",
    "application/3mf",
}

BLENDER_PATH: str = getattr(settings, "blender_path", "/opt/homebrew/bin/blender")

# ─────────────────────────────────────────────────────────────
# Ensure upload directories exist
# ─────────────────────────────────────────────────────────────
def get_model_dir(user_id: str) -> Path:
    path = BASE_UPLOAD_DIR / "users" / user_id / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def save_file(destination: Path, data: bytes):
    try:
        with open(destination, "wb") as buffer:
            buffer.write(data)
    except Exception as e:
        logger.exception(f"[ERROR] Saving file failed: {e}")
        raise HTTPException(500, "Failed to save file") from e


def validate_file_size(data: bytes, max_size: int):
    if len(data) > max_size:
        raise HTTPException(400, f"File too large (max {max_size // (1024*1024)} MB)")


def extract_model_metadata(filepath: Path) -> dict:
    """
    Run Blender script to extract metadata from the uploaded model.
    """
    log_path = filepath.with_suffix(".log")

    cmd = [
        BLENDER_PATH,
        "--background",
        "--python", "scripts/extract_model_metadata.py",
        "--", str(filepath)
    ]

    logger.info(f"🛠 Running Blender for metadata extraction: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        logger.error("❌ Blender executable not found.")
        raise HTTPException(500, "Blender executable not found on server") from e

    if result.returncode != 0:
        logger.error(f"❌ Blender exited with code {result.returncode}")
        logger.error(f"stdout:\n{result.stdout}")
        logger.error(f"stderr:\n{result.stderr}")
        _append_log(log_path, result.stdout, result.stderr)

        raise HTTPException(
            status_code=422,
            detail=f"Blender failed (code {result.returncode}). See log: {log_path}"
        )

    try:
        metadata = json.loads(result.stdout)
        logger.info(f"✅ Metadata extracted: {metadata}")
        return metadata
    except json.JSONDecodeError as e:
        logger.error("❌ Invalid JSON returned by Blender.")
        logger.error(f"stdout:\n{result.stdout}")
        logger.error(f"stderr:\n{result.stderr}")
        _append_log(log_path, result.stdout, result.stderr)

        raise HTTPException(
            status_code=422,
            detail=f"Blender returned invalid JSON. See log: {log_path}"
        )


def _append_log(log_path: Path, stdout: str, stderr: str):
    """
    Append stdout and stderr to a log file for debugging.
    """
    try:
        with open(log_path, "a") as logf:
            logf.write("\n===== Blender stdout =====\n")
            logf.write(stdout)
            logf.write("\n===== Blender stderr =====\n")
            logf.write(stderr)
        logger.info(f"📄 Blender output appended to log: {log_path}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to write Blender log file: {e}")


# ─────────────────────────────────────────────────────────────
# POST /api/v1/upload
# ─────────────────────────────────────────────────────────────
@router.post("/", response_model=ModelUploadResponse)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(None),
    description: str = Form(""),
    user: User = Depends(get_user_from_headers),
    db: Session = Depends(get_db),
):
    user_id = str(user.id)

    if not file.filename:
        raise HTTPException(400, "No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if not ext:
        raise HTTPException(400, "Missing file extension.")

    contents = await file.read()
    validate_file_size(contents, MAX_FILE_SIZE_BYTES)

    now = datetime.utcnow()
    now_iso = now.isoformat()

    if file.content_type not in ALLOWED_MODEL_TYPES:
        raise HTTPException(400, "Unsupported 3D model file type")

    model_id = str(uuid4())
    model_dir = get_model_dir(user_id)
    save_path = model_dir / f"{model_id}{ext}"
    logger.info(f"[MODEL] Saving model for user {user_id} to: {save_path}")

    save_file(save_path, contents)

    # ─────────────── Extract Metadata ───────────────
    metadata = extract_model_metadata(save_path)

    model = Model3D(
        id=model_id,
        name=name or file.filename,
        description=description,
        filename=file.filename,
        filepath=str(save_path.relative_to(BASE_UPLOAD_DIR)),
        uploader_id=user_id,
        uploaded_at=now,
        geometry_hash=metadata.get("geometry_hash"),
        is_duplicate=False,
        volume=metadata.get("volume"),
        bbox=json.dumps(metadata.get("bbox")),
        faces=metadata.get("faces"),
        vertices=metadata.get("vertices"),
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    logger.info(f"✅ Model {model.id} uploaded & metadata saved for user {user_id}")

    return ModelUploadResponse(
        id=model.id,
        name=model.name,
        url=f"{BASE_URL}/uploads/users/{user_id}/models/{model_id}{ext}",
        uploaded_at=now_iso,
    )
