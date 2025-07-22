# app/routes/models.py

import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse

from app.config.settings import settings
from pydantic import BaseModel

router = APIRouter(tags=["models"])

logger = logging.getLogger(__name__)


class ModelItem(BaseModel):
    username: str
    filename: str
    path: str
    url: str
    thumbnail_url: Optional[str]
    webm_url: Optional[str]


class PaginatedModelListResponse(BaseModel):
    models: List[ModelItem]
    page: int
    page_size: int
    total: int
    pages: int


@router.get(
    "/browse",
    summary="List all models from filesystem (all users) with pagination",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedModelListResponse,
)
async def browse_all_filesystem_models(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of models per page"),
) -> PaginatedModelListResponse:
    """
    Scan the uploads/users/*/models folders on disk and return paginated models.
    Includes username, model file path, optional thumbnail, and optional .webm turntable.
    """
    models_root = Path(settings.upload_dir) / "users"
    results: List[ModelItem] = []

    if not models_root.exists():
        logger.warning("📁 Models root %s does not exist.", models_root)
        return PaginatedModelListResponse(
            models=[],
            page=page,
            page_size=page_size,
            total=0,
            pages=0
        )

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

                model_data = ModelItem(
                    username=username,
                    filename=model_file.name,
                    path=model_rel_path,
                    url=model_url,
                    thumbnail_url=thumb_url,
                    webm_url=webm_url,
                )

                results.append(model_data)
                logger.debug("📝 Found model — user: %s file: %s", username, model_file.name)

    except Exception as e:
        logger.exception("❌ Error while scanning models.")
        raise

    results.sort(key=lambda m: (m.username, m.filename.lower()))

    total = len(results)
    pages = max(1, -(-total // page_size))  # ceil division
    if page > pages:
        page = pages

    start = (page - 1) * page_size
    end = start + page_size
    paginated = results[start:end]

    logger.info("✅ Returning page %d of %d (%d models total)", page, pages, total)

    return PaginatedModelListResponse(
        models=paginated,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages
    )


@router.get(
    "",
    summary="List all models (alias of /browse)",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedModelListResponse,
)
async def list_models(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of models per page"),
) -> PaginatedModelListResponse:
    """
    Alias for /browse endpoint.
    """
    return await browse_all_filesystem_models(page=page, page_size=page_size)
