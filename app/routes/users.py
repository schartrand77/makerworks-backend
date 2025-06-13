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
    db.commit
    
@router.get(
    "/admin/users",
    summary="List all users (admin only)",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.PublicUserOut],)
def admin_list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return [schemas.PublicUserOut.from_orm(u) for u in users]()