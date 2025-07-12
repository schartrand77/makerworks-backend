from pydantic import BaseModel, Field


class FilamentCreate(BaseModel):
    name: str
    type: str
    subtype: str | None = None
    surface: str | None = None
    texture: str | None = None

    color: str = Field(..., alias="colorHex")
    color_name: str | None = Field(None, alias="colorName")

    price_per_kg: float = Field(..., alias="pricePerKg")
    currency: str | None = "USD"
    description: str | None = None

    is_active: bool | None = True
    is_biodegradable: bool | None = None

    model_config = {"populate_by_name": True}


class FilamentUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    subtype: str | None = None
    surface: str | None = None
    texture: str | None = None

    color: str | None = Field(None, alias="colorHex")
    color_name: str | None = Field(None, alias="colorName")

    price_per_kg: float | None = Field(None, alias="pricePerKg")
    currency: str | None = None
    description: str | None = None

    is_active: bool | None = None
    is_biodegradable: bool | None = None

    model_config = {"populate_by_name": True}


class FilamentOut(BaseModel):
    id: int
    name: str
    type: str
    subtype: str | None = None
    surface: str | None = None
    texture: str | None = None

    color: str = Field(..., alias="colorHex")
    color_name: str | None = Field(None, alias="colorName")

    price_per_kg: float = Field(..., alias="pricePerKg")
    currency: str | None = "USD"
    description: str | None = None

    is_active: bool | None = True
    is_biodegradable: bool | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}
