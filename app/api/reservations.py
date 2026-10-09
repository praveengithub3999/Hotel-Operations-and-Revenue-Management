from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

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

@router.get("/availability/{room_id}")
def check_room_availability(
    room_id: int,
    check_in_date: date,
    check_out_date: date,
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(
        Room.id == room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    if check_in_date >= check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date"
        )

    overlapping_reservation = db.query(
        Reservation
    ).filter(
        Reservation.room_id == room_id,
        Reservation.status.in_([
            "PENDING",
            "CONFIRMED",
            "CHECKED_IN"
        ]),
        Reservation.check_in_date < check_out_date,
        Reservation.check_out_date > check_in_date
    ).first()

    if overlapping_reservation:
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
    response_model=ReservationResponse
)
def create_reservation(
    reservation: ReservationCreate,
    db: Session = Depends(get_db)
):
    # Check guest
    guest = db.query(Guest).filter(
        Guest.id == reservation.guest_id
    ).first()

    if not guest:
        raise HTTPException(
            status_code=404,
            detail="Guest not found"
        )

    # Check room
    room = db.query(Room).filter(
        Room.id == reservation.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    # Validate dates
    if reservation.check_in_date >= reservation.check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date"
        )

    # Check room status
    if room.status in ["OUT_OF_SERVICE", "MAINTENANCE"]:
        raise HTTPException(
            status_code=400,
            detail="Room is not available for reservation"
        )

    # Check overlapping reservations
    overlapping_reservation = db.query(
        Reservation
    ).filter(
        Reservation.room_id == reservation.room_id,
        Reservation.status.in_([
            "PENDING",
            "CONFIRMED",
            "CHECKED_IN"
        ]),
        Reservation.check_in_date < reservation.check_out_date,
        Reservation.check_out_date > reservation.check_in_date
    ).first()

    if overlapping_reservation:
        raise HTTPException(
            status_code=400,
            detail="Room is already reserved for these dates"
        )

    # Create reservation
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


@router.get(
    "/",
    response_model=list[ReservationResponse]
)
def get_reservations(
    db: Session = Depends(get_db)
):
    return db.query(Reservation).all()


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponse
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

@router.delete("/{reservation_id}")
def cancel_reservation(
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

    if reservation.status in [
        "CHECKED_IN",
        "CHECKED_OUT",
        "CANCELLED"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Reservation cannot be cancelled"
        )

    reservation.status = "CANCELLED"

    db.commit()
    db.refresh(reservation)

    return {
        "message": "Reservation cancelled successfully",
        "reservation_id": reservation.id,
        "status": reservation.status
    }

@router.post("/{reservation_id}/check-in")
def check_in_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    # Find reservation
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    # Reservation must be confirmed
    if reservation.status != "CONFIRMED":
        raise HTTPException(
            status_code=400,
            detail="Only confirmed reservations can be checked in"
        )

    # Check-in date validation
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

    # Find room
    room = db.query(Room).filter(
        Room.id == reservation.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    # Room cannot be under maintenance
    if room.status in [
        "MAINTENANCE",
        "OUT_OF_SERVICE"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Room is not available for check-in"
        )

    # Room should not already be occupied
    if room.status == "OCCUPIED":
        raise HTTPException(
            status_code=400,
            detail="Room is already occupied"
        )

    # Update reservation
    reservation.status = "CHECKED_IN"

    # Update room
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