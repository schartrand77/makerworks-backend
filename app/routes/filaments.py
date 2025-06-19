# app/routes/filaments.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.filaments import FilamentCreate, FilamentUpdate, FilamentOut
from app.models import Filament
from app.database import get_db
from app.schemas.users import UserOut
from app.dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/filaments",
    tags=["Filaments"],
)


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