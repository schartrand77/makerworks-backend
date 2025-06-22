from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate
from app.auth_service import hash_password


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, new_user: UserCreate) -> User:
    hashed_pw = hash_password(new_user.password)
    user = User(
        username=new_user.username,
        email=new_user.email,
        hashed_password=hashed_pw,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False