from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DiscountCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    discount_type: str = Field(default="PERCENTAGE")  # PERCENTAGE or FLAT
    value: Decimal = Field(gt=0)
    description: Optional[str] = None
    is_active: bool = True


class DiscountResponse(BaseModel):
    id: int
    code: str
    discount_type: str
    value: Decimal
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
