from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)

    guest_id = Column(
        Integer,
        ForeignKey("guests.id"),
        nullable=False
    )

    room_id = Column(
        Integer,
        ForeignKey("rooms.id"),
        nullable=False
    )

    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)

    number_of_guests = Column(Integer, nullable=False)

    status = Column(
        String(30),
        default="PENDING"
    )

    special_requests = Column(String(500))

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )