from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, index=True)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id"),
        nullable=False
    )

    status = Column(
        String,
        default="OPEN",
        nullable=False
    )

    reported_by = Column(
        String(100),
        nullable=True
    )

    category = Column(
        String(50),
        default="GENERAL",
        nullable=True
    )

    priority = Column(
        String(20),
        default="MEDIUM",
        nullable=True
    )

    issue = Column(
        String,
        nullable=False
    )

    description = Column(
        String(255),
        nullable=True
    )

    assigned_to = Column(
        String,
        nullable=True
    )

    notes = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    resolved_at = Column(
        DateTime,
        nullable=True
    )