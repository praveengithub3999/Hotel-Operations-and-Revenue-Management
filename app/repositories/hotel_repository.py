from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.models.room import Room
from app.repositories.base import BaseRepository


class HotelRepository(BaseRepository[Hotel]):
    def __init__(self, db: Session):
        super().__init__(Hotel, db)

    def find_by_name_and_city(self, name: str, city: str) -> Optional[Hotel]:
        return self.db.query(Hotel).filter(
            func.lower(Hotel.name) == name.strip().lower(),
            func.lower(Hotel.city) == city.strip().lower()
        ).first()


class RoomTypeRepository(BaseRepository[RoomType]):
    def __init__(self, db: Session):
        super().__init__(RoomType, db)

    def find_by_hotel_and_name(self, hotel_id: int, name: str) -> Optional[RoomType]:
        return self.db.query(RoomType).filter(
            RoomType.hotel_id == hotel_id,
            func.lower(RoomType.name) == name.strip().lower()
        ).first()

    def get_by_hotel(self, hotel_id: int) -> List[RoomType]:
        return self.db.query(RoomType).filter(RoomType.hotel_id == hotel_id).all()


class RoomRepository(BaseRepository[Room]):
    def __init__(self, db: Session):
        super().__init__(Room, db)

    def find_by_hotel_and_number(self, hotel_id: int, room_number: str) -> Optional[Room]:
        return self.db.query(Room).filter(
            Room.hotel_id == hotel_id,
            Room.room_number == room_number
        ).first()

    def get_rooms_by_filter(
        self,
        hotel_id: Optional[int] = None,
        room_type_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Room]:
        query = self.db.query(Room)
        if hotel_id is not None:
            query = query.filter(Room.hotel_id == hotel_id)
        if room_type_id is not None:
            query = query.filter(Room.room_type_id == room_type_id)
        if status is not None:
            query = query.filter(Room.status == status)
        return query.all()
