from pydantic import BaseModel, RootModel
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Query, Depends, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from app.db.database import get_async_db
from app.models.models import Filament
from app.schemas.filaments import FilamentOut
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Existing picker-related schemas & route remain unchanged


@router.get(
    "",
    summary="Get flat list of all filaments for Estimate page",
    status_code=status.HTTP_200_OK,
    response_model=List[FilamentOut],
)
async def list_filaments(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Return a flat list of all active filaments for estimate dropdown.
    """
    stmt = select(Filament).where(Filament.is_active == True)
    result = await db.execute(stmt)
    filaments = result.scalars().all()

    logger.info(f"✅ Returned {len(filaments)} filaments for Estimate page.")
    return filaments
