from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.room import Room
from app.repositories.hotel_repository import HotelRepository, RoomRepository, RoomTypeRepository
from app.repositories.reservation_repository import ReservationRepository
from app.schemas.room import RoomCreate, RoomUpdate

UNAVAILABLE_ROOM_STATUSES = [
    "DIRTY",
    "CLEANING",
    "MAINTENANCE",
    "OUT_OF_SERVICE",
    "OCCUPIED"
]


class RoomService:
    def __init__(self, db: Session):
        self.db = db
        self.room_repo = RoomRepository(db)
        self.hotel_repo = HotelRepository(db)
        self.room_type_repo = RoomTypeRepository(db)
        self.reservation_repo = ReservationRepository(db)

    def create_room(self, data: RoomCreate) -> Room:
        hotel = self.hotel_repo.get_by_id(data.hotel_id)
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")

        room_type = self.room_type_repo.get_by_id(data.room_type_id)
        if not room_type:
            raise HTTPException(status_code=404, detail="Room type not found")

        existing = self.room_repo.find_by_hotel_and_number(data.hotel_id, data.room_number)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Room number already exists in this hotel"
            )

        room = Room(
            hotel_id=data.hotel_id,
            room_type_id=data.room_type_id,
            room_number=data.room_number,
            floor=data.floor,
            status="AVAILABLE"
        )
        return self.room_repo.create(room)

    def get_rooms(self) -> List[Room]:
        return self.room_repo.get_all()

    def get_room_by_id(self, room_id: int) -> Room:
        room = self.room_repo.get_by_id(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return room

    def update_room(self, room_id: int, data: RoomUpdate) -> Room:
        room = self.room_repo.get_by_id(room_id, for_update=True)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if data.hotel_id is not None:
            hotel = self.hotel_repo.get_by_id(data.hotel_id)
            if not hotel:
                raise HTTPException(status_code=404, detail="Hotel not found")
            room.hotel_id = data.hotel_id

        if data.room_type_id is not None:
            room_type = self.room_type_repo.get_by_id(data.room_type_id)
            if not room_type:
                raise HTTPException(status_code=404, detail="Room type not found")
            room.room_type_id = data.room_type_id

        if data.room_number is not None and data.room_number != room.room_number:
            existing = self.room_repo.find_by_hotel_and_number(room.hotel_id, data.room_number)
            if existing and existing.id != room.id:
                raise HTTPException(
                    status_code=409,
                    detail="Room number already exists in this hotel"
                )
            room.room_number = data.room_number

        if data.floor is not None:
            room.floor = data.floor

        if data.status is not None:
            allowed = ["AVAILABLE", "RESERVED", "OCCUPIED", "DIRTY", "CLEANING", "OUT_OF_SERVICE", "MAINTENANCE"]
            if data.status not in allowed:
                raise HTTPException(status_code=400, detail=f"Invalid room status. Allowed: {allowed}")
            room.status = data.status

        return self.room_repo.update(room)

    def check_room_availability(
        self,
        room_id: int,
        check_in_date: date,
        check_out_date: date
    ) -> Dict[str, Any]:
        if check_in_date >= check_out_date:
            raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")

        room = self.room_repo.get_by_id(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.status in UNAVAILABLE_ROOM_STATUSES:
            return {
                "room_id": room_id,
                "available": False,
                "message": "Room is not currently ready for reservation"
            }

        overlapping = self.reservation_repo.find_overlapping(room_id, check_in_date, check_out_date)
        if overlapping:
            return {
                "room_id": room_id,
                "available": False,
                "message": "Room is already reserved for these dates"
            }

        return {
            "room_id": room_id,
            "available": True,
            "message": "Room is available"
        }

    def get_available_rooms(
        self,
        check_in_date: date,
        check_out_date: date,
        hotel_id: Optional[int] = None,
        room_type_id: Optional[int] = None
    ) -> List[Room]:
        """Find all available rooms for a given date range and optional hotel/room_type filters."""
        if check_in_date >= check_out_date:
            raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")

        candidate_rooms = self.room_repo.get_rooms_by_filter(
            hotel_id=hotel_id,
            room_type_id=room_type_id
        )

        available_rooms = []
        for room in candidate_rooms:
            if room.status in UNAVAILABLE_ROOM_STATUSES:
                continue
            overlapping = self.reservation_repo.find_overlapping(room.id, check_in_date, check_out_date)
            if not overlapping:
                available_rooms.append(room)

        return available_rooms

    def calculate_dynamic_price(self, room_type_id: int, stay_date: date) -> Decimal:
        """
        Dynamic room pricing (Section 28 Feature 1):
        - Weekends (Friday, Saturday): 20% surge (+20%)
        - Peak Season (October festival month & December holidays): +30%
        """
        room_type = self.room_type_repo.get_by_id(room_type_id)
        if not room_type:
            raise HTTPException(status_code=404, detail="Room type not found")

        base = Decimal(str(room_type.base_price))
        multiplier = Decimal("1.00")

        # Weekend surge: Friday (4) and Saturday (5)
        if stay_date.weekday() in (4, 5):
            multiplier += Decimal("0.20")

        # Peak season: October (10) and December (12)
        if stay_date.month in (10, 12):
            multiplier += Decimal("0.30")

        return (base * multiplier).quantize(Decimal("0.01"))
