from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomTypeCreate(BaseModel):
    hotel_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    capacity: int = Field(gt=0)
    base_price: Decimal = Field(
        ge=Decimal("0"),
        max_digits=10,
        decimal_places=2
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Room type name cannot be empty")
        return value


class RoomTypeResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    description: str | None
    capacity: int
    base_price: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)
