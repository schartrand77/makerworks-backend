# app/routes/models.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db  # FIXED: was app.db
from app.models import ModelMetadata
from app.utils.auth import get_current_user, TokenData

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/")
async def list_models(db: AsyncSession = Depends(get_db)):
    """
    List all uploaded models in descending order of upload time.
    """
    result = await db.execute(
        select(ModelMetadata).order_by(ModelMetadata.uploaded_at.desc())
    )
    models = result.scalars().all()

    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "uploader": m.uploader,
                "uploaded_at": m.uploaded_at.isoformat(),
                "preview_image": m.preview_image,
            }
            for m in models
        ]
    }


@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Delete a model by ID if the user is the owner or an admin.
    """
    result = await db.execute(
        select(ModelMetadata).where(ModelMetadata.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if user.sub != model.uploader and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this model")

    await db.delete(model)
    await db.commit()

    return {"status": "deleted", "model_id": model_id}