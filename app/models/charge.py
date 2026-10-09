from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class Charge(Base):
    __tablename__ = "charges"

    id = Column(Integer, primary_key=True, index=True)

    reservation_id = Column(
        Integer,
        ForeignKey("reservations.id"),
        nullable=False
    )

    charge_type = Column(
        String(50),
        nullable=False
    )

    description = Column(String(255))

    quantity = Column(
        Integer,
        nullable=False,
        default=1
    )

    unit_price = Column(
        Numeric(10, 2),
        nullable=False
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )