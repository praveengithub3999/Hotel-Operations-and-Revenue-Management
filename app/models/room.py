from sqlalchemy import Column, Integer, String, ForeignKey

from app.database.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    room_type_id = Column(Integer, ForeignKey("room_types.id"), nullable=False)
    room_number = Column(String(20), nullable=False)
    floor = Column(Integer, nullable=False)
    status = Column(String(30), default="AVAILABLE")