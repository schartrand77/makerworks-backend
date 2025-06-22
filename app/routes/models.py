# app/routes/models.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.model_metadata import ModelMetadata
from app.schemas.models import ModelOut
from app.schemas.token import TokenData
from app.dependencies import get_current_user

router = APIRouter(tags=["Models"])  # Removed prefix="/models"


@router.get(
    "/",
    summary="List uploaded models",
    status_code=status.HTTP_200_OK,
    response_model=dict
)
async def list_models(
    mine: bool = Query(False, description="Only return models uploaded by the current user"),
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    List all uploaded models.
    If 'mine' is true, only return models uploaded by the current user.
    """
    query = select(ModelMetadata).order_by(ModelMetadata.uploaded_at.desc())

    if mine:
        query = query.where(ModelMetadata.uploader == int(user.sub))

    result = await db.execute(query)
    models = result.scalars().all()

    return {
        "models": [
            ModelOut.model_validate(m).serialize(role=user.role)
            for m in models
        ]
    }


@router.get(
    "/duplicates",
    summary="List duplicate models (admin only)",
    status_code=status.HTTP_200_OK,
    response_model=dict
)
async def get_duplicates(
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    List all models marked as duplicates based on geometry hash.
    Only accessible by admin users.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(ModelMetadata).where(ModelMetadata.is_duplicate == True)
    )
    models = result.scalars().all()

    return {
        "duplicates": [
            ModelOut.model_validate(m).serialize(role="admin")
            for m in models
        ]
    }


@router.delete(
    "/{model_id}",
    summary="Delete a model (if owner or admin)",
    status_code=status.HTTP_200_OK,
)
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Delete a model by ID, if the user is the uploader or has admin role.
    """
    result = await db.execute(
        select(ModelMetadata).where(ModelMetadata.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if str(user.sub) != str(model.uploader) and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this model")

    await db.delete(model)
    await db.commit()

    return {"status": "deleted", "model_id": model_id}