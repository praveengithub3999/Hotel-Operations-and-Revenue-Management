from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MaintenanceCreate(BaseModel):
    room_id: int
    issue: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    status: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: int
    room_id: int
    status: str
    issue: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True