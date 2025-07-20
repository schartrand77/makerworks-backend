# app/routes/models.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pathlib import Path
from fastapi.responses import JSONResponse

from app.db.session import get_db
from app.dependencies.auth import get_user_from_headers
from app.models import ModelMetadata
from app.schemas.models import ModelOut
from app.schemas.token import TokenData
from app.config.settings import settings

router = APIRouter(tags=["Models"])


@router.get(
    "",
    summary="List uploaded models",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def list_models(
    mine: bool = Query(
        False, description="Only return models uploaded by the current user"
    ),
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_user_from_headers),
):
    """
    List all uploaded models from the database.
    If 'mine' is true, only return models uploaded by the current user.
    """
    query = select(ModelMetadata).order_by(ModelMetadata.uploaded_at.desc())

    if mine:
        query = query.where(ModelMetadata.uploader == user.sub)

    result = await db.execute(query)
    models = result.scalars().all()

    return {
        "models": [
            ModelOut.model_validate(m).serialize(
                role="admin" if "admin" in user.groups else "user"
            )
            for m in models
        ]
    }


@router.get(
    "/duplicates",
    summary="List duplicate models (admin only)",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def get_duplicates(
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_user_from_headers),
):
    """
    List all models marked as duplicates based on geometry hash.
    Only accessible by admin users.
    """
    if "admin" not in user.groups:
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(ModelMetadata).where(ModelMetadata.is_duplicate.is_(True))
    )
    models = result.scalars().all()

    return {
        "duplicates": [
            ModelOut.model_validate(m).serialize(role="admin") for m in models
        ]
    }


@router.delete(
    "/{model_id}",
    summary="Delete a model (if owner or admin)",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_user_from_headers),
):
    """
    Delete a model by ID, if the user is the uploader or has admin role.
    """
    result = await db.execute(select(ModelMetadata).where(ModelMetadata.id == model_id))
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    is_admin = "admin" in user.groups
    is_owner = str(model.uploader) == str(user.sub)

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this model"
        )

    await db.delete(model)
    await db.commit()

    return {"status": "deleted", "model_id": model_id}


@router.get(
    "/browse",
    summary="List all models from filesystem (all users)",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def browse_all_filesystem_models():
    """
    Scan the uploads/users/*/models folders on disk and return all models found.
    Includes username, model file path, and optional thumbnail.
    """
    models_root = Path(settings.upload_dir) / "users"
    result = []

    if not models_root.exists():
        return {"models": []}

    for user_dir in models_root.iterdir():
        if not user_dir.is_dir():
            continue

        username = user_dir.name
        models_dir = user_dir / "models"

        if not models_dir.exists():
            continue

        for model_file in models_dir.glob("*.stl"):
            model_rel_path = model_file.relative_to(settings.upload_dir).as_posix()
            model_url = f"/uploads/{model_rel_path}"

            # Look for a thumbnail in same folder (optional)
            thumb_file = model_file.with_suffix(".png")
            thumb_url = None
            if thumb_file.exists():
                thumb_rel_path = thumb_file.relative_to(settings.upload_dir).as_posix()
                thumb_url = f"/uploads/{thumb_rel_path}"

            result.append({
                "username": username,
                "filename": model_file.name,
                "path": model_rel_path,
                "url": model_url,
                "thumbnail_url": thumb_url,
            })

    return {"models": result}