# app/schemas/checkout.py

from pydantic import BaseModel, Field
from typing import List, Optional


class CheckoutItem(BaseModel):
    model_id: int = Field(..., description="Unique ID of the model being purchased")
    name: str = Field(..., max_length=100, description="Human-readable name of the model")
    cost: float = Field(..., gt=0.0, description="Cost of the model in USD")

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=200, description="Description or cart note")
    total_cost: float = Field(..., gt=0.0, lt=10000.0, description="Total purchase cost in USD")
    items: List[CheckoutItem] = Field(..., description="List of models being checked out")
    currency: Optional[str] = Field(default="USD", description="Currency code (ISO 4217 format)")

    model_config = {"from_attributes": True}