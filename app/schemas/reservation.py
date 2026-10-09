from datetime import date
from pydantic import BaseModel


class ReservationCreate(BaseModel):
    guest_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    number_of_guests: int
    special_requests: str | None = None


class ReservationResponse(BaseModel):
    id: int
    guest_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    number_of_guests: int
    status: str
    special_requests: str | None

    class Config:
        from_attributes = True