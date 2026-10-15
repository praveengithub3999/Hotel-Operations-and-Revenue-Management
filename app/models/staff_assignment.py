from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database.database import Base


class StaffAssignment(Base):
    __tablename__ = "staff_assignments"

    id = Column(Integer, primary_key=True, index=True)
    staff_username = Column(String(100), nullable=False, index=True)
    staff_role = Column(String(50), nullable=False)
    assigned_entity = Column(String(50), nullable=False)  # "ROOM" or "MAINTENANCE_REQUEST"
    entity_id = Column(Integer, nullable=False)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
