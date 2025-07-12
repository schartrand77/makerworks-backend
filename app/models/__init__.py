# app/models/__init__.py

from app.db import Base
from app.models.models import (
    Estimate,
    EstimateSettings,
    Favorite,
    Filament,
    ModelMetadata,
    User,
)

# Optional alias for compatibility
Model3D = ModelMetadata

__all__ = [
    "Estimate",
    "EstimateSettings",
    "Favorite",
    "Filament",
    "Model3D",
    "ModelMetadata",
    "User",
]
