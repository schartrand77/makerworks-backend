from app.schemas.estimate import EstimateRequest, EstimateResponse
from sqlalchemy.orm import Session
from app.models.model_metadata import ModelMetadata
from app.models.filament_pricing import FilamentPricing

PROFILE_SPEEDS = {
    "standard": 8.0,
    "quality": 5.0,
    "elite": 3.5,
}

def calculate_estimate(data: EstimateRequest, db: Session) -> EstimateResponse:
    # Get model volume from database (already extracted from geometry)
    model = db.query(ModelMetadata).filter(ModelMetadata.id == data.model_id).first()
    if not model:
        raise ValueError("Model not found.")

    volume_mm3 = model.volume_mm3

    # Get filament price
    filament = db.query(FilamentPricing).filter(FilamentPricing.name == data.filament_type).first()
    if not filament:
        raise ValueError("Filament not found.")

    grams = volume_mm3 * filament.density
    cost = grams * filament.price_per_gram

    # Custom text fee (optional)
    if data.custom_text:
        cost += filament.custom_text_fee or 2.00  # fallback default

    # Time estimate
    speed = PROFILE_SPEEDS.get(data.print_profile, 5.0)
    minutes = volume_mm3 / (speed * 60)

    return EstimateResponse(
        estimated_time_minutes=round(minutes, 2),
        estimated_cost_usd=round(cost, 2)
    )
