# app/routes/filaments.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.models import Filament
from app.database import get_db
from app.routes.auth import get_current_user
from app.schemas import UserOut

router = APIRouter(prefix="/api/v1/filaments", tags=["Filaments"])


# --------- Schemas ---------

class FilamentCreate(BaseModel):
    name: str
    type: str
    color: str
    price_per_kg: float
    is_active: Optional[bool] = True


class FilamentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    color: Optional[str] = None
    price_per_kg: Optional[float] = None
    is_active: Optional[bool] = None


class FilamentOut(BaseModel):
    id: int
    name: str
    type: str
    color: str
    price_per_kg: float

    class Config:
        orm_mode = True


# --------- Routes ---------

@router.get(
    "/",
    summary="List all active filaments",
    status_code=status.HTTP_200_OK,
    response_model=List[FilamentOut],
)
def list_filaments(db: Session = Depends(get_db)):
    """
    Return all active filament types in the system.
    """
    return db.query(Filament).filter(Filament.is_active == True).all()


@router.post(
    "/",
    summary="Add a new filament (admin only)",
    status_code=status.HTTP_201_CREATED,
    response_model=FilamentOut,
)
def add_filament(
    filament: FilamentCreate,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")

    new_filament = Filament(**filament.dict())
    db.add(new_filament)
    db.commit()
    db.refresh(new_filament)
    return new_filament


@router.put(
    "/{fid}",
    summary="Update a filament (admin only)",
    status_code=status.HTTP_200_OK,
    response_model=FilamentOut,
)
def update_filament(
    fid: int,
    updates: FilamentUpdate,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")

    filament = db.query(Filament).filter(Filament.id == fid).first()
    if not filament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filament not found.")

    for field, value in updates.dict(exclude_unset=True).items():
        setattr(filament, field, value)

    db.commit()
    db.refresh(filament)
    return filament


@router.delete(
    "/{fid}",
    summary="Soft-delete a filament (admin only)",
    status_code=status.HTTP_200_OK,
)
def delete_filament(
    fid: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")

    filament = db.query(Filament).filter(Filament.id == fid).first()
    if not filament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filament not found.")

    filament.is_active = False
    db.commit()
    return {"deleted": True, "id": filament.id}