from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal
    payment_method: str
    transaction_reference: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: Decimal
    payment_method: str
    payment_status: str
    transaction_reference: Optional[str] = None

    class Config:
        from_attributes = True