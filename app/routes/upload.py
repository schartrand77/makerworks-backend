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

import trimesh

router = APIRouter()
logger = logging.getLogger(__name__)

BASE_URL: str = getattr(settings, "base_url", "http://localhost:8000").rstrip("/")
BASE_UPLOAD_DIR: Path = Path(settings.upload_dir)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_MODEL_TYPES = {
    "application/octet-stream",
    "application/vnd.ms-pki.stl",
    "model/stl",
    "application/3mf",
}
PLACEHOLDER_GLB = Path("uploads/placeholders/placeholder.glb")
PLACEHOLDER_PNG = Path("uploads/placeholders/placeholder.png")


def get_model_dir(user_id: str) -> Path:
    path = BASE_UPLOAD_DIR / "users" / user_id / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


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
    log_path = filepath.with_suffix(".log")
    script_path = Path(__file__).parent.parent / "scripts" / "extract_model_metadata.py"
    if not script_path.exists():
        logger.warning(f"⚠️ Metadata extractor missing, skipping.")
        return {}
    cmd = ["python3", str(script_path.resolve()), "--", str(filepath.resolve())]
    logger.info(f"🛠 Running metadata extractor: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning(f"⚠️ Metadata extractor failed. stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        _append_log(log_path, result.stdout, result.stderr)
        return {}
    try:
        metadata = json.loads(result.stdout)
        logger.info(f"✅ Metadata extracted: {metadata}")
        return metadata
    except json.JSONDecodeError:
        logger.warning("⚠️ Invalid JSON from metadata extractor.")
        _append_log(log_path, result.stdout, result.stderr)
        return {}


def convert_to_glb(filepath: Path) -> Path:
    glb_path = filepath.with_suffix(".glb")
    try:
        mesh = trimesh.load(filepath, force='mesh')
        mesh.export(glb_path, file_type='glb')
        if not glb_path.exists():
            logger.warning(f"⚠️ .glb was not created, falling back.")
            return PLACEHOLDER_GLB.relative_to(BASE_UPLOAD_DIR)
        logger.info(f"✅ .glb created: {glb_path}")
        return glb_path.relative_to(BASE_UPLOAD_DIR)
    except Exception as e:
        logger.warning(f"⚠️ Failed to convert to .glb: {e}, using placeholder.")
        return PLACEHOLDER_GLB.relative_to(BASE_UPLOAD_DIR)


def render_thumbnail(filepath: Path) -> Path:
    script_path = Path(__file__).parent.parent / "utils" / "render_thumbnail.py"
    if not script_path.exists():
        logger.warning(f"⚠️ Thumbnail renderer missing, using placeholder.")
        return PLACEHOLDER_PNG.relative_to(BASE_UPLOAD_DIR)
    cmd = ["python3", str(script_path.resolve()), "--", str(filepath.resolve())]
    logger.info(f"🖼 Rendering thumbnail: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning(f"⚠️ Thumbnail renderer failed. stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return PLACEHOLDER_PNG.relative_to(BASE_UPLOAD_DIR)
    thumb_path = filepath.with_suffix(".png")
    if not thumb_path.exists():
        logger.warning("⚠️ Thumbnail file not found after rendering.")
        return PLACEHOLDER_PNG.relative_to(BASE_UPLOAD_DIR)
    logger.info(f"✅ .png thumbnail created: {thumb_path}")
    return thumb_path.relative_to(BASE_UPLOAD_DIR)


def _append_log(log_path: Path, stdout: str, stderr: str):
    try:
        with open(log_path, "a") as logf:
            logf.write("\n===== stdout =====\n")
            logf.write(stdout)
            logf.write("\n===== stderr =====\n")
            logf.write(stderr)
        logger.info(f"📄 Output appended to log: {log_path}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to write log file: {e}")


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

    metadata = extract_model_metadata(save_path)
    glb_rel_path = convert_to_glb(save_path)
    thumbnail_rel_path = render_thumbnail(save_path)

    model_kwargs = {
        "id": model_id,
        "name": name or file.filename,
        "description": description,
        "filename": file.filename,
        "filepath": str(save_path.relative_to(BASE_UPLOAD_DIR)),
        "uploader_id": user_id,
        "uploaded_at": now,
        "geometry_hash": metadata.get("geometry_hash"),
        "is_duplicate": False,
        "volume": metadata.get("volume", None),
        "bbox": json.dumps(metadata.get("bbox", [])),
        "faces": metadata.get("faces", 0),
        "vertices": metadata.get("vertices", 0),
        "thumbnail_url": f"{BASE_URL}/uploads/{thumbnail_rel_path}"
    }

    model = Model3D(**model_kwargs)

    db.add(model)
    db.commit()
    db.refresh(model)

    logger.info(f"✅ Model {model.id} uploaded & metadata + glb + thumbnail saved for user {user_id}")

    return ModelUploadResponse(
        id=model.id,
        name=model.name,
        url=f"{BASE_URL}/uploads/users/{user_id}/models/{model_id}{ext}",
        uploaded_at=now_iso,
        glb_url=f"{BASE_URL}/uploads/{glb_rel_path}",
        thumbnail_url=f"{BASE_URL}/uploads/{thumbnail_rel_path}"
    )
