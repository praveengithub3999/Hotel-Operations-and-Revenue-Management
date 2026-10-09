from pydantic import BaseModel


class GuestCreate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    id_type: str | None = None
    id_reference: str | None = None


class GuestResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    address: str | None
    id_type: str | None
    id_reference: str | None

    class Config:
        from_attributes = True