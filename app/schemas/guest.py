from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional


class GuestCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, min_length=7, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)
    id_type: Optional[str] = Field(default=None, max_length=50)
    id_reference: Optional[str] = Field(default=None, max_length=100)
    emergency_contact: Optional[str] = Field(default=None, max_length=50)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if not value:
                return None
        return value


class GuestResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    id_type: Optional[str]
    id_reference: Optional[str]
    emergency_contact: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
