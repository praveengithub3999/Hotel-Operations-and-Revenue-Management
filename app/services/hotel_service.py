from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.repositories.hotel_repository import HotelRepository, RoomTypeRepository
from app.schemas.hotel import HotelCreate
from app.schemas.room_type import RoomTypeCreate


class HotelService:
    def __init__(self, db: Session):
        self.db = db
        self.hotel_repo = HotelRepository(db)
        self.room_type_repo = RoomTypeRepository(db)

    def create_hotel(self, hotel_data: HotelCreate) -> Hotel:
        existing = self.hotel_repo.find_by_name_and_city(
            hotel_data.name, hotel_data.city
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="A hotel with this name already exists in this city"
            )

        hotel = Hotel(
            name=hotel_data.name.strip(),
            address=hotel_data.address.strip(),
            city=hotel_data.city.strip(),
            contact_number=hotel_data.contact_number.strip() if hotel_data.contact_number else None
        )
        return self.hotel_repo.create(hotel)

    def get_hotels(self) -> List[Hotel]:
        return self.hotel_repo.get_all()

    def get_hotel_by_id(self, hotel_id: int) -> Hotel:
        if hotel_id <= 0:
            raise HTTPException(status_code=400, detail="Hotel ID must be greater than zero")
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")
        return hotel

    def create_room_type(self, data: RoomTypeCreate) -> RoomType:
        hotel = self.hotel_repo.get_by_id(data.hotel_id)
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")

        existing = self.room_type_repo.find_by_hotel_and_name(data.hotel_id, data.name)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="This room type already exists for this hotel"
            )

        room_type = RoomType(
            hotel_id=data.hotel_id,
            name=data.name.strip(),
            description=data.description,
            capacity=data.capacity,
            base_price=data.base_price
        )
        return self.room_type_repo.create(room_type)

    def get_room_types(self) -> List[RoomType]:
        return self.room_type_repo.get_all()

    def get_room_type_by_id(self, room_type_id: int) -> RoomType:
        room_type = self.room_type_repo.get_by_id(room_type_id)
        if not room_type:
            raise HTTPException(status_code=404, detail="Room type not found")
        return room_type
