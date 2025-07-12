# app/routes/filaments.py


from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_async_db
from app.dependencies.auth import assert_user_is_admin, get_user_from_headers
from app.models import Filament, User
from app.schemas.filaments import FilamentCreate, FilamentOut, FilamentUpdate

router = APIRouter()


# ─────────────────────────────────────────────────────────────
# GET /filaments/ — List all active filaments
# ─────────────────────────────────────────────────────────────
@router.get(
    "/",
    summary="List all active filaments",
    status_code=status.HTTP_200_OK,
    response_model=list[FilamentOut],
    response_model_exclude_none=True,
)
async def list_filaments(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Filament).where(Filament.is_active == True))
    return result.scalars().all()


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
async def add_filament(
    filament: FilamentCreate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_user_from_headers),
):
    await assert_user_is_admin(user)
    new_filament = Filament(**filament.dict())
    db.add(new_filament)
    await db.commit()
    await db.refresh(new_filament)
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
async def update_filament(
    fid: int,
    updates: FilamentUpdate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_user_from_headers),
):
    await assert_user_is_admin(user)
    result = await db.execute(select(Filament).where(Filament.id == fid))
    filament = result.scalar_one_or_none()

    if not filament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Filament not found."
        )

    for field, value in updates.dict(exclude_unset=True).items():
        setattr(filament, field, value)

    await db.commit()
    await db.refresh(filament)
    return filament


# ─────────────────────────────────────────────────────────────
# DELETE /filaments/{fid} — Soft-delete filament by ID
# ─────────────────────────────────────────────────────────────
@router.delete(
    "/{fid}",
    summary="Soft-delete a filament (admin only)",
    status_code=status.HTTP_200_OK,
)
async def delete_filament(
    fid: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_user_from_headers),
):
    await assert_user_is_admin(user)
    result = await db.execute(select(Filament).where(Filament.id == fid))
    filament = result.scalar_one_or_none()

    if not filament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Filament not found."
        )

    filament.is_active = False
    await db.commit()
    return {"deleted": True, "id": filament.id}


# ─────────────────────────────────────────────────────────────
# GET /filaments/picker — Return nested data for frontend fanout picker
# ─────────────────────────────────────────────────────────────
@router.get(
    "/picker",
    summary="Get filament picker data for frontend",
    status_code=status.HTTP_200_OK,
)
async def get_filament_picker_data(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Filament).where(Filament.is_active == True))
    filaments = result.scalars().all()
    picker: dict[str, Any] = {}

    for f in filaments:
        category = f.type or "Uncategorized"
        subtype = f.subtype or "Default"
        if category not in picker:
            picker[category] = {}
        if subtype not in picker[category]:
            picker[category][subtype] = {"colors": []}
        picker[category][subtype]["colors"].append(
            {
                "id": f.id,
                "name": f.color_name or f.color,
                "hex": f.color,
                "pricePerKg": f.price_per_kg,
                "isBiodegradable": f.is_biodegradable or False,
            }
        )

    return picker
