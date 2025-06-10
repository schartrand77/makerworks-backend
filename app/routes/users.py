from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=schemas.UserOut)
def get_user_profile(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return user

@router.put("/me", response_model=schemas.UserOut)
def update_user_profile(update: schemas.UserUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    for field, value in update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(db: Session = Depends(get_db), user=Depends(get_current_user)):
    db.delete(user)
    db.commit()