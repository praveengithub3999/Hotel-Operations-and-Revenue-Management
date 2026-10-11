
from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)

    payment_id = Column(
        Integer,
        ForeignKey("payments.id"),
        nullable=False
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False,
        default="SUCCESS"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
