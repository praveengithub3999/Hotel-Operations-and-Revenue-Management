from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class InvoiceCreate(BaseModel):
    reservation_id: int
    discount: Decimal = Decimal("0")
    tax_percentage: Decimal


class InvoiceResponse(BaseModel):
    id: int
    reservation_id: int
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    status: str
    issued_at: datetime

    class Config:
        from_attributes = True