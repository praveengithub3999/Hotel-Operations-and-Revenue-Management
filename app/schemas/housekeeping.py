from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class HousekeepingCreate(BaseModel):
    room_id: int
    assigned_to: Optional[str] = None
    task_type: Optional[str] = "CLEANING"
    priority: Optional[str] = "MEDIUM"
    notes: Optional[str] = None
    remarks: Optional[str] = None


class HousekeepingUpdate(BaseModel):
    status: str
    assigned_to: Optional[str] = None
    task_type: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    remarks: Optional[str] = None


class HousekeepingResponse(BaseModel):
    id: int
    room_id: int
    status: str
    assigned_to: Optional[str] = None
    task_type: Optional[str] = "CLEANING"
    priority: Optional[str] = "MEDIUM"
    notes: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)