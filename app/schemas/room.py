from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomCreate(BaseModel):
    hotel_id: int = Field(gt=0)
    room_type_id: int = Field(gt=0)
    room_number: str = Field(min_length=1, max_length=50)
    floor: int = Field(ge=0)

    @field_validator("room_number")
    @classmethod
    def validate_room_number(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Room number cannot be empty")

        return value


class RoomResponse(BaseModel):
    id: int
    hotel_id: int
    room_type_id: int
    room_number: str
    floor: int
    status: str

    model_config = ConfigDict(from_attributes=True)
