from pydantic import BaseModel, Field
from typing import Optional, List


class EstimateRequest(BaseModel):
    model_id: int
    x_mm: float = Field(..., gt=0)
    y_mm: float = Field(..., gt=0)
    z_mm: float = Field(..., gt=0)
    filament_type: str
    filament_colors: List[str]
    print_profile: str  # "standard", "quality", "elite"
    custom_text: Optional[str] = None


class EstimateResponse(BaseModel):
    estimated_time_minutes: float
    estimated_cost_usd: float