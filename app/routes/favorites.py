# app/routes/favorites.py

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_user_from_headers
from app.models import Favorite, ModelMetadata, User
from app.schemas import ModelOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get(
    "/",
    summary="Get current user's favorited models",
    status_code=status.HTTP_200_OK,
    response_model=list[ModelOut],
)
async def get_user_favorites(
    db: Session = Depends(get_db),
    user: User = Depends(get_user_from_headers),
):
    """
    Retrieve all models favorited by the currently authenticated user.
    """
    logger.info("🔷 Fetching favorites for user_id=%s", user.id)

    result = (
        db.query(ModelMetadata)
        .join(Favorite, Favorite.model_id == ModelMetadata.id)
        .filter(Favorite.user_id == user.id)
        .all()
    )

    logger.debug("✅ Found %d favorites for user %s", len(result), user.username)

    return [
        ModelOut.model_validate(m).serialize(
            role="admin" if user.role == "admin" else "user"
        )
        for m in result
    ]


@router.post(
    "/{model_id}",
    summary="Add model to favorites",
    status_code=status.HTTP_201_CREATED,
)
async def add_to_favorites(
    model_id: int = Path(..., description="Model ID to favorite"),
    db: Session = Depends(get_db),
    user: User = Depends(get_user_from_headers),
):
    """
    Add a model to the authenticated user's favorites list.
    """
    logger.info("➕ Adding model_id=%s to user_id=%s favorites", model_id, user.id)

    # Check model exists
    model = db.query(ModelMetadata).filter_by(id=model_id).first()
    if not model:
        logger.warning("❌ Model %s not found", model_id)
        raise HTTPException(status_code=404, detail="Model not found")

    exists = db.query(Favorite).filter_by(user_id=user.id, model_id=model_id).first()
    if exists:
        logger.info("⚠️ Model %s already in favorites for user %s", model_id, user.username)
        return {"detail": "Already favorited"}

    db.add(Favorite(user_id=user.id, model_id=model_id))
    db.commit()

    logger.info("✅ Added model %s to favorites for user %s", model_id, user.username)
    return {"detail": "Model added to favorites"}


@router.delete(
    "/{model_id}",
    summary="Remove model from favorites",
    status_code=status.HTTP_200_OK,
)
async def remove_from_favorites(
    model_id: int = Path(..., description="Model ID to remove from favorites"),
    db: Session = Depends(get_db),
    user: User = Depends(get_user_from_headers),
):
    """
    Remove a model from the user's favorites list.
    """
    logger.info("➖ Removing model_id=%s from user_id=%s favorites", model_id, user.id)

    favorite = db.query(Favorite).filter_by(user_id=user.id, model_id=model_id).first()
    if not favorite:
        logger.warning("❌ Favorite model %s not found for user %s", model_id, user.username)
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(favorite)
    db.commit()

    logger.info("✅ Removed model %s from favorites for user %s", model_id, user.username)
    return {"detail": "Model removed from favorites"}
