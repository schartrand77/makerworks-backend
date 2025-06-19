from pydantic import BaseModel, Field

class CheckoutRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)
    total_cost: float = Field(..., gt=0.0, lt=10000.0)