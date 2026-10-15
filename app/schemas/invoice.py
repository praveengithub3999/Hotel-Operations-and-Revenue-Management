from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class InvoiceCreate(BaseModel):
    reservation_id: int
    discount: Decimal = Decimal("0")
    tax_percentage: Decimal = Field(
        default=Decimal("10"),
        ge=0,
        le=100
    )


class InvoiceResponse(BaseModel):
    id: int
    reservation_id: int
    subtotal: Decimal
    discount: Decimal
    tax_percentage: Decimal
    tax: Decimal
    total: Decimal
    status: str
    issued_at: datetime

    model_config = ConfigDict(from_attributes=True)
