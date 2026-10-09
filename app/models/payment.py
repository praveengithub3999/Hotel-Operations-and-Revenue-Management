from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False
    )

    amount = Column(Numeric(10, 2), nullable=False)

    payment_method = Column(String, nullable=False)

    payment_status = Column(
        String,
        default="SUCCESS",
        nullable=False
    )

    transaction_reference = Column(
        String,
        nullable=True
    )

    paid_at = Column(
        DateTime,
        default=datetime.utcnow
    )