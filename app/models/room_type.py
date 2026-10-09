from sqlalchemy import Column, Integer, String, Numeric, ForeignKey

from app.database.database import Base


class RoomType(Base):
    __tablename__ = "room_types"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    capacity = Column(Integer, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), default="ACTIVE")