from pydantic import BaseModel


class RoomCreate(BaseModel):
    hotel_id: int
    room_type_id: int
    room_number: str
    floor: int


class RoomResponse(BaseModel):
    id: int
    hotel_id: int
    room_type_id: int
    room_number: str
    floor: int
    status: str

    class Config:
        from_attributes = True