from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HousekeepingCreate(BaseModel):
    room_id: int
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class HousekeepingUpdate(BaseModel):
    status: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class HousekeepingResponse(BaseModel):
    id: int
    room_id: int
    status: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True