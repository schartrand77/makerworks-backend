"""Filesystem utilities used across the project."""

from pathlib import Path
import uuid
import logging
import trimesh

from app.config.settings import settings

UPLOADS_ROOT = settings.uploads_path

logger = logging.getLogger(__name__)


def create_user_folders(user_id: uuid.UUID) -> dict[str, bool]:
    """
    Create avatar and models folders for the given user ID.
    Returns a dict with path strings and bool success flags.
    """
    user_dir = UPLOADS_ROOT / str(user_id)
    avatars_dir = user_dir / "avatars"
    models_dir = user_dir / "models"

    result: dict[str, bool] = {}

    for path in [avatars_dir, models_dir]:
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created folder: {path}")
            result[str(path)] = True
        except Exception as e:
            logger.error(f"❌ Failed to create folder {path}: {e}")
            result[str(path)] = False

    return result


def ensure_user_model_thumbnails(user_id: str) -> None:
    """Scan a user's models directory and generate missing thumbnails."""
    models_dir = UPLOADS_ROOT / "users" / str(user_id) / "models"
    if not models_dir.exists():
        logger.debug(f"📁 Models directory does not exist for user {user_id}: {models_dir}")
        return

    for model_file in models_dir.iterdir():
        if not model_file.is_file():
            continue
        if model_file.suffix.lower() not in {".stl", ".3mf"}:
            continue
        if model_file.name.startswith(".") or model_file.name.startswith("~"):
            continue

        thumb_file = model_file.with_suffix(".png")
        if thumb_file.exists():
            continue

        try:
            mesh = trimesh.load(str(model_file), force="mesh")
            scene = mesh.scene()
            png = scene.save_image(resolution=(512, 512), visible=False)
            if png:
                with open(thumb_file, "wb") as f:
                    f.write(png)
                logger.info(f"🖼️ Generated thumbnail for {model_file.name}")
        except Exception as e:
            logger.exception(f"❌ Failed to create thumbnail for {model_file}: {e}")

