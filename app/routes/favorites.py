# app/routes/favorites.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models import Favorite, ModelMetadata
from app.schemas import ModelOut
from app.schemas.token import TokenPayload

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get(
    "/",
    summary="Get current user's favorited models",
    status_code=status.HTTP_200_OK,
    response_model=list[ModelOut],
)
async def get_user_favorites(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Retrieve all models favorited by the currently authenticated user.
    """
    result = await db.execute(
        select(ModelMetadata)
        .join(Favorite, Favorite.model_id == ModelMetadata.id)
        .filter(Favorite.user_id == user.sub)
    )
    models = result.scalars().all()

    return [
        ModelOut.model_validate(m).serialize(
            role="admin" if "admin" in user.groups else "user"
        )
        for m in models
    ]


@router.post(
    "/{model_id}",
    summary="Add model to favorites",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def add_to_favorites(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Add a model to the authenticated user's favorites list.
    """
    result = await db.execute(
        select(Favorite).filter_by(user_id=user.sub, model_id=model_id)
    )
    exists = result.scalar_one_or_none()
    if not exists:
        db.add(Favorite(user_id=user.sub, model_id=model_id))
        await db.commit()


@router.delete(
    "/{model_id}",
    summary="Remove model from favorites",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def remove_from_favorites(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Remove a model from the user's favorites list.
    """
    result = await db.execute(
        select(Favorite).filter_by(user_id=user.sub, model_id=model_id)
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    await db.delete(favorite)
    await db.commit()
