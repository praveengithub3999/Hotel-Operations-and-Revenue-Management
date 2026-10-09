from pydantic import BaseModel
from decimal import Decimal


class RefundCreate(BaseModel):
    payment_id: int
    amount: Decimal