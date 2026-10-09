from datetime import datetime
from pydantic import BaseModel


class ServiceRequestCreate(BaseModel):
    reservation_id: int
    service_type: str
    description: str | None = None
    quantity: int = 1


class ServiceRequestUpdate(BaseModel):
    status: str


class ServiceRequestResponse(BaseModel):
    id: int
    reservation_id: int
    room_id: int
    guest_id: int
    service_type: str
    description: str | None
    quantity: int
    status: str
    requested_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True