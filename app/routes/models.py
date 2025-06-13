# app/routes/models.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import ModelMetadata
from app.schemas import ModelOut
from app.utils.auth import get_current_user, TokenData

router = APIRouter(prefix="/api/v1/models", tags=["Models"])


@router.get(
    "/",
    summary="List all uploaded models",
    status_code=status.HTTP_200_OK,
)
async def list_models(
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    List all uploaded models in reverse chronological order.
    Response shape depends on user role (admin sees more metadata).
    """
    result = await db.execute(
        select(ModelMetadata).order_by(ModelMetadata.uploaded_at.desc())
    )
    models = result.scalars().all()

    return {
        "models": [
            ModelOut.from_orm(m).serialize(role=user.role)
            for m in models
        ]
    }


@router.get(
    "/duplicates",
    summary="List duplicate models (admin only)",
    status_code=status.HTTP_200_OK,
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
            ModelOut.from_orm(m).serialize(role="admin")
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

    if str(user.sub) != model.uploader and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this model")

    await db.delete(model)
    await db.commit()

    return {"status": "deleted", "model_id": model_id}