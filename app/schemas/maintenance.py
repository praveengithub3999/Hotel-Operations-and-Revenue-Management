from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class MaintenanceCreate(BaseModel):
    room_id: int
    issue: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = "GENERAL"
    priority: Optional[str] = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    reported_by: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    status: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: int
    room_id: int
    status: str
    issue: str
    description: Optional[str] = None
    category: Optional[str] = "GENERAL"
    priority: Optional[str] = "MEDIUM"
    reported_by: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)