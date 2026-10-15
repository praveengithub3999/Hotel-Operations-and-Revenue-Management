from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime
from app.database.database import Base


class Discount(Base):
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    discount_type = Column(String(20), default="PERCENTAGE", nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
