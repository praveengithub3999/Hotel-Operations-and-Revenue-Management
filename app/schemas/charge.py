from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ChargeCreate(BaseModel):
    reservation_id: int
    charge_type: str
    description: str | None = None
    quantity: int
    unit_price: Decimal


class ChargeResponse(BaseModel):
    id: int
    reservation_id: int
    charge_type: str
    description: str | None
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True