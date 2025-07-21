from fastapi import APIRouter, status
from pathlib import Path
from fastapi.responses import JSONResponse
from app.config.settings import settings

import logging

router = APIRouter(tags=["Models"])

logger = logging.getLogger(__name__)


@router.get(
    "/browse",
    summary="List all models from filesystem (all users)",
    status_code=status.HTTP_200_OK,
)
async def browse_all_filesystem_models() -> JSONResponse:
    """
    Scan the uploads/users/*/models folders on disk and return all models found.
    Includes username, model file path, optional thumbnail, and optional .webm turntable.
    """
    models_root = Path(settings.upload_dir) / "users"
    results: list[dict] = []

    if not models_root.exists():
        logger.warning("📁 Models root %s does not exist.", models_root)
        return JSONResponse(status_code=200, content={"models": []})

    logger.info("📁 Scanning models under: %s", models_root.resolve())

    try:
        for user_dir in models_root.iterdir():
            if not user_dir.is_dir():
                continue

            username = user_dir.name
            models_dir = user_dir / "models"

            if not models_dir.exists():
                continue

            for model_file in models_dir.iterdir():
                if not model_file.is_file():
                    continue

                if model_file.suffix.lower() not in [".stl", ".obj", ".3mf"]:
                    continue

                if model_file.name.startswith(".") or model_file.name.startswith("~"):
                    continue

                try:
                    model_rel_path = model_file.relative_to(settings.upload_dir).as_posix()
                except ValueError:
                    logger.warning("⚠️ Skipping suspicious path: %s", model_file)
                    continue

                model_url = f"/uploads/{model_rel_path}"

                # Optional thumbnail
                thumb_url = None
                thumb_file = model_file.with_suffix(".png")
                if thumb_file.exists():
                    try:
                        thumb_rel_path = thumb_file.relative_to(settings.upload_dir).as_posix()
                        thumb_url = f"/uploads/{thumb_rel_path}"
                    except ValueError:
                        logger.warning("⚠️ Skipping thumbnail with bad path: %s", thumb_file)

                # Optional webm turntable
                webm_url = None
                webm_file = model_file.with_suffix(".webm")
                if webm_file.exists():
                    try:
                        webm_rel_path = webm_file.relative_to(settings.upload_dir).as_posix()
                        webm_url = f"/uploads/{webm_rel_path}"
                    except ValueError:
                        logger.warning("⚠️ Skipping webm with bad path: %s", webm_file)

                model_data = {
                    "username": username,
                    "filename": model_file.name,
                    "path": model_rel_path,
                    "url": model_url,
                    "thumbnail_url": thumb_url,
                    "webm_url": webm_url,
                }

                results.append(dict(model_data))
                logger.debug(
                    "📝 Found model — user: %s file: %s",
                    username,
                    model_file.name
                )

    except Exception as e:
        logger.exception("❌ Error while scanning models.")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error while scanning models.", "error": str(e)},
        )

    results.sort(key=lambda m: (m["username"], m["filename"].lower()))

    logger.info("✅ Found %d models on disk.", len(results))
    return JSONResponse(status_code=200, content={"models": results})


@router.get(
    "",
    summary="List all models (alias of /browse)",
    status_code=status.HTTP_200_OK,
)
async def list_models() -> JSONResponse:
    """
    Alias for /browse endpoint.
    """
    return await browse_all_filesystem_models()
