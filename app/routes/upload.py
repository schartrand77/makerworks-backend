import logging
import subprocess
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.database import get_db
from app.dependencies.auth import get_user_from_headers
from app.models import ModelMetadata as Model3D
from app.schemas.models import ModelUploadResponse
from app.schemas.token import TokenData

router = APIRouter()

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
        logging.error(f"[ERROR] Saving file failed: {e}")
        raise HTTPException(500, "Failed to save file") from e


def validate_file_size(data: bytes, max_size: int):
    if len(data) > max_size:
        raise HTTPException(400, f"File too large (max {max_size // (1024*1024)} MB)")


def extract_model_metadata(filepath: Path) -> dict:
    """
    Run Blender script to extract metadata from the uploaded model.
    """
    try:
        result = subprocess.run(
            [
                "blender", "--background", "--python", "scripts/extract_model_metadata.py",
                "--", str(filepath)
            ],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"[MODEL] Blender metadata extraction failed: {e.stderr}")
        raise HTTPException(500, "Failed to extract model metadata")
    except json.JSONDecodeError:
        logging.error("[MODEL] Invalid JSON returned by Blender.")
        raise HTTPException(500, "Invalid metadata format from Blender")


# ─────────────────────────────────────────────────────────────
# POST /api/v1/upload
# ─────────────────────────────────────────────────────────────
@router.post("/", response_model=ModelUploadResponse)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(None),
    description: str = Form(""),
    token: TokenData = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db),
):
    user_id = token.sub

    if not file.filename:
        raise HTTPException(400, "No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if not ext:
        raise HTTPException(400, "Missing file extension.")

    contents = await file.read()
    validate_file_size(contents, MAX_FILE_SIZE_BYTES)

    now = datetime.utcnow()
    now_iso = now.isoformat()

    # ─────────────── Upload Model ───────────────
    if file.content_type not in ALLOWED_MODEL_TYPES:
        raise HTTPException(400, "Unsupported 3D model file type")

    model_id = str(uuid4())
    model_dir = get_model_dir(user_id)
    save_path = model_dir / f"{model_id}{ext}"
    logging.info(f"[MODEL] Saving model for user {user_id} to: {save_path}")

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
        is_duplicate=False,  # You can implement duplicate detection if desired
        volume=metadata.get("volume"),
        bbox=json.dumps(metadata.get("bbox")),  # store as JSON string
        faces=metadata.get("faces"),
        vertices=metadata.get("vertices"),
    )

    db.add(model)
    await db.commit()
    await db.refresh(model)

    return ModelUploadResponse(
        id=model.id,
        name=model.name,
        url=f"{BASE_URL}/uploads/users/{user_id}/models/{model_id}{ext}",
        uploaded_at=now_iso,
    )