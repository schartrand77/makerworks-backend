from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ModelMetadata, Favorite
from app.routes.auth import get_current_user
from app.schemas import UserOut, ModelOut

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("/", response_model=list[ModelOut])
def get_user_favorites(
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    """
    Return all models the current user has favorited.
    """
    favorites = (
        db.query(ModelMetadata)
        .join(Favorite, Favorite.model_id == ModelMetadata.id)
        .filter(Favorite.user_id == user.id)
        .all()
    )
    return favorites


@router.post("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_to_favorites(
    model_id: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    """
    Add a model to the current user's favorites.
    """
    exists = db.query(Favorite).filter_by(user_id=user.id, model_id=model_id).first()
    if exists:
        return  # Already a favorite — no-op
    favorite = Favorite(user_id=user.id, model_id=model_id)
    db.add(favorite)
    db.commit()


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_favorites(
    model_id: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    """
    Remove a model from the user's favorites.
    """
    favorite = db.query(Favorite).filter_by(user_id=user.id, model_id=model_id).first()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(favorite)
    db.commit()