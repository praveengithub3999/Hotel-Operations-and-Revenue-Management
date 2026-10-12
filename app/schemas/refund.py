from decimal import Decimal

from pydantic import BaseModel, Field


class RefundCreate(BaseModel):
    payment_id: int = Field(gt=0)
    amount: Decimal = Field(
        gt=Decimal("0"),
        max_digits=10,
        decimal_places=2
    )