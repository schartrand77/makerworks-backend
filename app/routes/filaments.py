# app/routes/filaments.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import Filament
from app.database import get_db
from app.routes.auth import get_current_user
from app.schemas import UserOut

from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/filaments", tags=["filaments"])


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


# --------- Routes ---------

@router.get("/", response_model=list[dict])
def list_filaments(db: Session = Depends(get_db)):
    """List all active filaments"""
    filaments = db.query(Filament).filter(Filament.is_active == True).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "type": f.type,
            "color": f.color,
            "price_per_kg": f.price_per_kg,
        }
        for f in filaments
    ]


@router.post("/", response_model=dict)
def add_filament(
    filament: FilamentCreate,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    f = Filament(**filament.dict())
    db.add(f)
    db.commit()
    db.refresh(f)
    return {"id": f.id, "name": f.name}


@router.put("/{fid}", response_model=dict)
def update_filament(
    fid: int,
    updates: FilamentUpdate,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    filament = db.query(Filament).get(fid)
    if not filament:
        raise HTTPException(status_code=404, detail="Filament not found.")
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(filament, field, value)
    db.commit()
    db.refresh(filament)
    return {
        "id": filament.id,
        "name": filament.name,
        "updated": True,
    }


@router.delete("/{fid}", response_model=dict)
def delete_filament(
    fid: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    filament = db.query(Filament).get(fid)
    if not filament:
        raise HTTPException(status_code=404, detail="Filament not found.")
    filament.is_active = False
    db.commit()
    return {"deleted": True, "id": filament.id}