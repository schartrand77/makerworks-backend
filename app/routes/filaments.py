# app/routes/filaments.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.filaments import FilamentCreate, FilamentUpdate, FilamentOut
from app.models import Filament
from app.db.database import get_db
from app.dependencies import get_current_admin

router = APIRouter(
    prefix="/filaments",
    tags=["Filaments"],
)

# ─────────────────────────────────────────────────────────────
# GET /filaments/ — List all active filaments
# ─────────────────────────────────────────────────────────────
@router.get(
    "/",
    summary="List all active filaments",
    status_code=status.HTTP_200_OK,
    response_model=List[FilamentOut],
    response_model_exclude_none=True,
)
def list_filaments(db: Session = Depends(get_db)):
    return db.query(Filament).filter(Filament.is_active == True).all()

# ─────────────────────────────────────────────────────────────
# POST /filaments/ — Create new filament (admin only)
# ─────────────────────────────────────────────────────────────
@router.post(
    "/",
    summary="Add a new filament (admin only)",
    status_code=status.HTTP_201_CREATED,
    response_model=FilamentOut,
    response_model_exclude_none=True,
)
def add_filament(
    filament: FilamentCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    new_filament = Filament(**filament.dict(by_alias=True))
    db.add(new_filament)
    db.commit()
    db.refresh(new_filament)
    return new_filament

# ─────────────────────────────────────────────────────────────
# PUT /filaments/{fid} — Update filament by ID (admin only)
# ─────────────────────────────────────────────────────────────
@router.put(
    "/{fid}",
    summary="Update a filament (admin only)",
    status_code=status.HTTP_200_OK,
    response_model=FilamentOut,
    response_model_exclude_none=True,
)
def update_filament(
    fid: int,
    updates: FilamentUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    filament = db.query(Filament).filter(Filament.id == fid).first()
    if not filament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filament not found.")

    for field, value in updates.dict(exclude_unset=True, by_alias=True).items():
        setattr(filament, field, value)

    db.commit()
    db.refresh(filament)
    return filament

# ─────────────────────────────────────────────────────────────
# DELETE /filaments/{fid} — Soft-delete filament by ID
# ─────────────────────────────────────────────────────────────
@router.delete(
    "/{fid}",
    summary="Soft-delete a filament (admin only)",
    status_code=status.HTTP_200_OK,
)
def delete_filament(
    fid: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    filament = db.query(Filament).filter(Filament.id == fid).first()
    if not filament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filament not found.")

    filament.is_active = False
    db.commit()
    return {"deleted": True, "id": filament.id}

# ─────────────────────────────────────────────────────────────
# GET /filaments/picker — Return nested data for frontend fanout picker
# ─────────────────────────────────────────────────────────────
@router.get(
    "/picker",
    summary="Get filament picker data for frontend",
    status_code=status.HTTP_200_OK,
)
def get_filament_picker_data(db: Session = Depends(get_db)):
    filaments = db.query(Filament).filter(Filament.is_active == True).all()
    result = {}

    for f in filaments:
        category = f.type
        subtype = f.subtype or "Default"
        if category not in result:
            result[category] = {}
        if subtype not in result[category]:
            result[category][subtype] = {"colors": []}
        result[category][subtype]["colors"].append({
            "name": f.color_name or f.color,
            "hex": f.color or "#CCCCCC"
        })

    return result