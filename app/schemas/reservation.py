from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReservationCreate(BaseModel):
    guest_id: int = Field(gt=0)
    room_id: int = Field(gt=0)
    check_in_date: date
    check_out_date: date
    number_of_guests: int = Field(gt=0)
    special_requests: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_in_date >= self.check_out_date:
            raise ValueError(
                "Check-out date must be after check-in date"
            )
        return self


class ReservationUpdate(BaseModel):
    room_id: int | None = None
    check_in_date: date | None = None
    check_out_date: date | None = None
    number_of_guests: int | None = None
    special_requests: str | None = None
    status: str | None = None


class ReservationResponse(BaseModel):
    id: int
    guest_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    number_of_guests: int
    status: str
    special_requests: str | None

    model_config = ConfigDict(from_attributes=True)