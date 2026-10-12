
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    reservation_id = Column(
        Integer,
        ForeignKey("reservations.id"),
        nullable=False
    )

    subtotal = Column(
        Numeric(10, 2),
        nullable=False
    )

    discount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    tax_percentage = Column(
        Numeric(5, 2),
        nullable=False,
        default=10
    )

    tax = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    total = Column(
        Numeric(10, 2),
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False,
        default="UNPAID"
    )

    issued_at = Column(
        DateTime,
        default=datetime.utcnow
    )
