from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentCreate(BaseModel):
    invoice_id: int = Field(gt=0)
    amount: Decimal = Field(
        gt=Decimal("0"),
        max_digits=10,
        decimal_places=2
    )
    payment_method: str
    transaction_reference: Optional[str] = None

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value: str) -> str:
        allowed_methods = [
            "CASH",
            "CARD",
            "UPI",
            "BANK_TRANSFER"
        ]

        value = value.strip().upper()

        if value not in allowed_methods:
            raise ValueError("Invalid payment method")

        return value


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: Decimal
    payment_method: str
    payment_status: str
    transaction_reference: Optional[str] = None
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
