# app/models/__init__.py

from app.db import Base
from app.models.models import (
    User,
    ModelMetadata,
    Favorite,
    Filament,
    EstimateSettings,
    Estimate,
)

# Optional alias for compatibility
Model3D = ModelMetadata

__all__ = [
    "User",
    "ModelMetadata",
    "Model3D",
    "Favorite",
    "Filament",
    "EstimateSettings",
    "Estimate",
]