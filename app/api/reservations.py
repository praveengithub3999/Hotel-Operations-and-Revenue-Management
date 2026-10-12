from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.core.roles import require_role
from app.database.database import get_db
from app.models.guest import Guest
from app.models.room import Room
from app.models.reservation import Reservation
from app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse
)

router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"]
)

ACTIVE_STATUSES = ["PENDING", "CONFIRMED", "CHECKED_IN"]
UNAVAILABLE_ROOM_STATUSES = [
    "DIRTY",
    "CLEANING",
    "MAINTENANCE",
    "OUT_OF_SERVICE",
    "OCCUPIED"
]


def has_overlapping_reservation(
    db: Session,
    room_id: int,
    check_in_date: date,
    check_out_date: date,
    exclude_id: int | None = None
):
    query = db.query(Reservation).filter(
        Reservation.room_id == room_id,
        Reservation.status.in_(ACTIVE_STATUSES),
        Reservation.check_in_date < check_out_date,
        Reservation.check_out_date > check_in_date
    )

    if exclude_id is not None:
        query = query.filter(Reservation.id != exclude_id)

    return query.first()


@router.get(
    "/availability/{room_id}",
    dependencies=[
        Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))
    ]
)
def check_room_availability(
    room_id: int,
    check_in_date: date,
    check_out_date: date,
    db: Session = Depends(get_db)
):
    if check_in_date >= check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date"
        )

    room = db.query(Room).filter(Room.id == room_id).first()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.status in UNAVAILABLE_ROOM_STATUSES:
        return {
            "room_id": room_id,
            "available": False,
            "message": "Room is not currently ready for reservation"
        }

    overlapping = has_overlapping_reservation(
        db, room_id, check_in_date, check_out_date
    )

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


@router.post(
    "/",
    response_model=ReservationResponse,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def create_reservation(
    reservation: ReservationCreate,
    db: Session = Depends(get_db)
):
    try:
        guest = db.query(Guest).filter(
            Guest.id == reservation.guest_id
        ).first()

        if not guest:
            raise HTTPException(status_code=404, detail="Guest not found")

        # Lock the room row to coordinate simultaneous bookings.
        room = db.query(Room).filter(
            Room.id == reservation.room_id
        ).with_for_update().first()

        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.status in UNAVAILABLE_ROOM_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Room is not currently ready for reservation"
            )

        overlapping = has_overlapping_reservation(
            db,
            reservation.room_id,
            reservation.check_in_date,
            reservation.check_out_date
        )

        if overlapping:
            raise HTTPException(
                status_code=400,
                detail="Room is already reserved for these dates"
            )

        new_reservation = Reservation(
            guest_id=reservation.guest_id,
            room_id=reservation.room_id,
            check_in_date=reservation.check_in_date,
            check_out_date=reservation.check_out_date,
            number_of_guests=reservation.number_of_guests,
            status="CONFIRMED",
            special_requests=reservation.special_requests
        )

        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)

        return new_reservation

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get(
    "/",
    response_model=list[ReservationResponse],
    dependencies=[
        Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))
    ]
)
def get_reservations(db: Session = Depends(get_db)):
    return db.query(Reservation).all()


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponse,
    dependencies=[
        Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))
    ]
)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    return reservation


@router.delete(
    "/{reservation_id}",
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    try:
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id
        ).with_for_update().first()

        if not reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )

        if reservation.status not in ["PENDING", "CONFIRMED"]:
            raise HTTPException(
                status_code=400,
                detail="Only pending or confirmed reservations can be cancelled"
            )

        reservation.status = "CANCELLED"
        db.commit()

        return {
            "message": "Reservation cancelled successfully",
            "reservation_id": reservation.id,
            "status": reservation.status
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.post(
    "/{reservation_id}/check-in",
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def check_in_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    try:
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id
        ).with_for_update().first()

        if not reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )

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

        room = db.query(Room).filter(
            Room.id == reservation.room_id
        ).with_for_update().first()

        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.status in UNAVAILABLE_ROOM_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Room is not ready for check-in"
            )

        overlapping = has_overlapping_reservation(
            db,
            reservation.room_id,
            reservation.check_in_date,
            reservation.check_out_date,
            exclude_id=reservation.id
        )

        if overlapping and overlapping.status == "CHECKED_IN":
            raise HTTPException(
                status_code=400,
                detail="Another active reservation is already checked into this room"
            )

        reservation.status = "CHECKED_IN"
        room.status = "OCCUPIED"

        db.commit()
        db.refresh(reservation)
        db.refresh(room)

        return {
            "message": "Guest checked in successfully",
            "reservation_id": reservation.id,
            "room_id": room.id,
            "reservation_status": reservation.status,
            "room_status": room.status
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
