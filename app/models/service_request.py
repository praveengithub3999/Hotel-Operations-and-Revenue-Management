from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)

    reservation_id = Column(
        Integer,
        ForeignKey("reservations.id"),
        nullable=False
    )

    room_id = Column(
        Integer,
        ForeignKey("rooms.id"),
        nullable=False
    )

    guest_id = Column(
        Integer,
        ForeignKey("guests.id"),
        nullable=False
    )

    service_type = Column(
        String(50),
        nullable=False
    )

    description = Column(String(255))

    quantity = Column(Integer, nullable=False, default=1)

    status = Column(
        String(30),
        nullable=False,
        default="REQUESTED"
    )

    requested_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    completed_at = Column(DateTime, nullable=True)