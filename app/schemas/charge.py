from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class ChargeCreate(BaseModel):
    reservation_id: int = Field(gt=0)
    charge_type: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(
        ge=Decimal("0"),
        max_digits=10,
        decimal_places=2
    )


class ChargeResponse(BaseModel):
    id: int
    reservation_id: int
    charge_type: str
    description: str | None
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
