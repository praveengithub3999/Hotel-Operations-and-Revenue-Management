from pydantic import BaseModel


class RoomTypeCreate(BaseModel):
    hotel_id: int
    name: str
    description: str | None = None
    capacity: int
    base_price: float


class RoomTypeResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    description: str | None
    capacity: int
    base_price: float
    status: str

    class Config:
        from_attributes = True