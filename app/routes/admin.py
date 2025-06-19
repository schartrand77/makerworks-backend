from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.users import UserOut  # ✅
from typing import List

router = APIRouter()


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


@router.get("/users", response_model=List[UserOut])
def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin-only: List all registered users.
    """
    require_admin(current_user)
    return db.query(User).all()