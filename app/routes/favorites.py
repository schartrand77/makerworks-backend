from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ModelMetadata, Favorite
from app.routes.auth import get_current_user
from app.schemas import UserOut, ModelOut

router = APIRouter(prefix="/api/v1/favorites", tags=["Favorites"])


@router.get(
    "/",
    response_model=list[ModelOut],
    summary="Get current user's favorited models",
    status_code=status.HTTP_200_OK,
)
def get_user_favorites(
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    """
    Retrieve all models favorited by the currently authenticated user.
    """
    favorites = (
        db.query(ModelMetadata)
        .join(Favorite, Favorite.model_id == ModelMetadata.id)
        .filter(Favorite.user_id == user.id)
        .all()
    )
    return favorites


@router.post(
    "/{model_id}",
    summary="Add model to favorites",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def add_to_favorites(
    model_id: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    """
    Add a model to the authenticated user's favorites list.
    """
    exists = db.query(Favorite).filter_by(user_id=user.id, model_id=model_id).first()
    if not exists:
        favorite = Favorite(user_id=user.id, model_id=model_id)
        db.add(favorite)
        db.commit()


@router.delete(
    "/{model_id}",
    summary="Remove model from favorites",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def remove_from_favorites(
    model_id: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    """
    Remove a model from the user's favorites list.
    """
    favorite = db.query(Favorite).filter_by(user_id=user.id, model_id=model_id).first()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(favorite)
    db.commit()