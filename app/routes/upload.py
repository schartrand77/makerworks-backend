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

BASE_URL: str = getattr(settings, "base_url", "http://localhost:8000").rstrip("/")
BASE_UPLOAD_DIR: Path = Path(settings.upload_dir)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_MODEL_TYPES = {
    "application/octet-stream",
    "application/vnd.ms-pki.stl",
    "model/stl",
    "application/3mf",
}


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
    """
    Run the metadata extractor script.
    """
    log_path = filepath.with_suffix(".log")

    script_path = Path(__file__).parent.parent / "scripts" / "extract_model_metadata.py"
    if not script_path.exists():
        logger.error(f"❌ Metadata extractor script not found at {script_path}")
        raise HTTPException(500, f"Metadata extractor script missing: {script_path}")

    cmd = [
        "python3",
        str(script_path.resolve()),
        "--",
        str(filepath.resolve())
    ]

    logger.info(f"🛠 Running metadata extractor: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        logger.error("❌ Python executable not found.")
        raise HTTPException(500, "Python not found") from e

    if result.returncode != 0:
        logger.error(f"❌ Metadata extractor exited with code {result.returncode}")
        logger.error(f"stdout:\n{result.stdout}")
        logger.error(f"stderr:\n{result.stderr}")
        _append_log(log_path, result.stdout, result.stderr)

        raise HTTPException(
            status_code=422,
            detail=f"Metadata extractor failed (code {result.returncode}). See log: {log_path}"
        )

    try:
        metadata = json.loads(result.stdout)
        logger.info(f"✅ Metadata extracted: {metadata}")
        return metadata
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON returned by metadata extractor.")
        _append_log(log_path, result.stdout, result.stderr)
        raise HTTPException(422, f"Metadata extractor returned invalid JSON. See log: {log_path}")


def render_webm(filepath: Path) -> Path:
    """
    Run the turntable renderer to generate a .webm preview.
    """
    webm_path = filepath.with_suffix(".webm")
    script_path = Path(__file__).parent.parent / "utils" / "render_turntable_webm.py"
    if not script_path.exists():
        logger.error(f"❌ Turntable renderer script not found at {script_path}")
        raise HTTPException(500, f"Turntable renderer script missing: {script_path}")

    cmd = [
        "python3",
        str(script_path.resolve()),
        "--",
        str(filepath.resolve()),
    ]

    logger.info(f"🎥 Rendering .webm preview: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        logger.error("❌ Python executable not found for webm renderer.")
        raise HTTPException(500, "Python not found") from e

    if result.returncode != 0:
        logger.error(f"❌ Webm renderer exited with code {result.returncode}")
        logger.error(f"stdout:\n{result.stdout}")
        logger.error(f"stderr:\n{result.stderr}")
        raise HTTPException(
            status_code=422,
            detail=f"Webm renderer failed (code {result.returncode})."
        )

    logger.info(f"✅ .webm created at {webm_path}")
    return webm_path.relative_to(BASE_UPLOAD_DIR)


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

    # ─────────────── Extract Metadata ───────────────
    metadata = extract_model_metadata(save_path)

    # ─────────────── Render .webm ───────────────
    webm_rel_path = render_webm(save_path)

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
        "volume": None,
        "bbox": None,
        "faces": 0,
        "vertices": 0,
    }

    if ext == ".3mf":
        model_kwargs["description"] += "\n3MF Metadata:\n" + json.dumps(metadata, indent=2)
        logger.info(f"📋 Saved 3MF metadata: {metadata}")
    else:
        model_kwargs.update({
            "volume": metadata.get("volume"),
            "bbox": json.dumps(metadata.get("bbox", [])),
            "faces": metadata.get("faces", 0),
            "vertices": metadata.get("vertices", 0),
        })

    model = Model3D(**model_kwargs)

    db.add(model)
    db.commit()
    db.refresh(model)

    logger.info(f"✅ Model {model.id} uploaded & metadata + webm saved for user {user_id}")

    return ModelUploadResponse(
        id=model.id,
        name=model.name,
        url=f"{BASE_URL}/uploads/users/{user_id}/models/{model_id}{ext}",
        uploaded_at=now_iso,
        webm_url=f"{BASE_URL}/uploads/{webm_rel_path}",
    )
