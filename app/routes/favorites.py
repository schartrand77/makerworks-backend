# app/routes/favorites.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_user_from_headers
from app.models import Favorite, ModelMetadata, User
from app.schemas import ModelOut

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
    result = (
        db.query(ModelMetadata)
        .join(Favorite, Favorite.model_id == ModelMetadata.id)
        .filter(Favorite.user_id == user.id)
        .all()
    )

    return [
        ModelOut.model_validate(m).serialize(
            role="admin" if user.role == "admin" else "user"
        )
        for m in result
    ]


@router.post(
    "/{model_id}",
    summary="Add model to favorites",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def add_to_favorites(
    model_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_user_from_headers),
):
    """
    Add a model to the authenticated user's favorites list.
    """
    exists = db.query(Favorite).filter_by(user_id=user.id, model_id=model_id).first()
    if not exists:
        db.add(Favorite(user_id=user.id, model_id=model_id))
        db.commit()


@router.delete(
    "/{model_id}",
    summary="Remove model from favorites",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def remove_from_favorites(
    model_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_user_from_headers),
):
    """
    Remove a model from the user's favorites list.
    """
    favorite = db.query(Favorite).filter_by(user_id=user.id, model_id=model_id).first()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(favorite)
    db.commit()
