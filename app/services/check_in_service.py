from datetime import date
from typing import Any, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.room import Room
from app.models.reservation import Reservation
from app.repositories.hotel_repository import RoomRepository
from app.repositories.reservation_repository import ReservationRepository
from app.utils.audit_logger import create_audit_log

UNAVAILABLE_ROOM_STATUSES = [
    "DIRTY",
    "CLEANING",
    "MAINTENANCE",
    "OUT_OF_SERVICE"
]


class CheckInService:
    def __init__(self, db: Session):
        self.db = db
        self.reservation_repo = ReservationRepository(db)
        self.room_repo = RoomRepository(db)

    def check_in_guest(self, reservation_id: int) -> Dict[str, Any]:
        # Lock reservation
        reservation = self.reservation_repo.get_by_id(reservation_id, for_update=True)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if reservation.status != "CONFIRMED":
            raise HTTPException(
                status_code=400,
                detail="Only confirmed reservations can be checked in"
            )

        today = date.today()
        if today < reservation.check_in_date:
            raise HTTPException(
                status_code=400,
                detail="Check-in date has not arrived yet"
            )

        if today >= reservation.check_out_date:
            raise HTTPException(
                status_code=400,
                detail="Reservation has already passed"
            )

        # Lock room row
        room = self.room_repo.get_by_id(reservation.room_id, for_update=True)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.status in UNAVAILABLE_ROOM_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Room is not ready for check-in"
            )

        overlapping = self.reservation_repo.find_overlapping(
            room_id=reservation.room_id,
            check_in_date=reservation.check_in_date,
            check_out_date=reservation.check_out_date,
            exclude_id=reservation.id,
            for_update=True
        )
        if overlapping and overlapping.status == "CHECKED_IN":
            raise HTTPException(
                status_code=400,
                detail="Another active reservation is already checked into this room"
            )

        reservation.status = "CHECKED_IN"
        room.status = "OCCUPIED"

        self.db.commit()
        self.db.refresh(reservation)
        self.db.refresh(room)

        create_audit_log(
            action="CHECK_IN",
            message=f"Guest checked in to room {room.room_number}",
            reservation_id=reservation.id,
            entity="reservation",
            entity_id=reservation.id,
            details={"room": room.room_number, "room_id": room.id}
        )

        return {
            "message": "Guest checked in successfully",
            "reservation_id": reservation.id,
            "room_id": room.id,
            "reservation_status": reservation.status,
            "room_status": room.status
        }
