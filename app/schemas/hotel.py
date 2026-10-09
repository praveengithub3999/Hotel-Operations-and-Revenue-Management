from pydantic import BaseModel


class HotelCreate(BaseModel):
    name: str
    address: str
    city: str
    contact_number: str | None = None


class HotelResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    contact_number: str | None
    status: str

    class Config:
        from_attributes = True