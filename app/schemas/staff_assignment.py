from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StaffAssignmentCreate(BaseModel):
    staff_username: str = Field(min_length=1, max_length=100)
    staff_role: str = Field(pattern="^(HOUSEKEEPING|MAINTENANCE)$")
    assigned_entity: str = Field(pattern="^(ROOM|MAINTENANCE_REQUEST)$")
    entity_id: int
    notes: Optional[str] = None


class StaffAssignmentResponse(BaseModel):
    id: int
    staff_username: str
    staff_role: str
    assigned_entity: str
    entity_id: int
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
