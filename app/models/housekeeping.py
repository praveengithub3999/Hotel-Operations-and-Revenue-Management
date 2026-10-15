from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class Housekeeping(Base):
    __tablename__ = "housekeeping"

    id = Column(Integer, primary_key=True, index=True)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id"),
        nullable=False
    )

    status = Column(
        String,
        default="DIRTY",
        nullable=False
    )

    assigned_to = Column(
        String,
        nullable=True
    )

    task_type = Column(
        String(50),
        default="CLEANING",
        nullable=True
    )

    priority = Column(
        String(20),
        default="MEDIUM",
        nullable=True
    )

    notes = Column(
        String,
        nullable=True
    )

    remarks = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    started_at = Column(
        DateTime,
        nullable=True
    )

    completed_at = Column(
        DateTime,
        nullable=True
    )