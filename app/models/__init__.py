# app/models/__init__.py

from app.models.base import Base
from app.models.models import (
    Estimate,
    # EstimateSettings,  # commented out if not yet defined
    Favorite,
    Filament,
    ModelMetadata,
    User,
)

# Optional alias for compatibility
Model3D = ModelMetadata

__all__ = [
    "Base",
    "Estimate",
    # "EstimateSettings",  # include here if/when implemented
    "Favorite",
    "Filament",
    "Model3D",
    "ModelMetadata",
    "User",
]