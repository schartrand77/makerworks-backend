# app/models/__init__.py

from app.db.base import Base
from app.models.models import (
    Estimate,
    EstimateSettings,
    Favorite,
    Filament,
    FilamentPricing,
    ModelMetadata,
    User,
)

# Optional alias for compatibility
Model3D = ModelMetadata

__all__ = [
    "Base",
    "Estimate",
    "EstimateSettings",
    "Favorite",
    "Filament",
    "FilamentPricing",
    "Model3D",
    "ModelMetadata",
    "User",
]