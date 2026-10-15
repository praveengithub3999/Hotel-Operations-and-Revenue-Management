from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)