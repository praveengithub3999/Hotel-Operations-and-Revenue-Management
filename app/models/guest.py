from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.database import Base


class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150))
    phone = Column(String(20))
    address = Column(String(255))
    id_type = Column(String(50))
    id_reference = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)