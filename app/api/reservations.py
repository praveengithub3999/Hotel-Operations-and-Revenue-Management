from datetime import date
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.reservation import (
    ReservationCreate,
    ReservationUpdate,
    ReservationResponse
)
from app.services.reservation_service import ReservationService
from app.services.check_in_service import CheckInService
from app.services.check_out_service import CheckOutService
from app.services.room_service import RoomService

router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"]
)


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
    service = RoomService(db)
    return service.check_room_availability(room_id, check_in_date, check_out_date)


@router.post(
    "/",
    response_model=ReservationResponse,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def create_reservation(
    reservation: ReservationCreate,
    db: Session = Depends(get_db)
):
    service = ReservationService(db)
    return service.create_reservation(reservation)


@router.get(
    "/",
    response_model=List[ReservationResponse],
    dependencies=[
        Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))
    ]
)
def get_reservations(db: Session = Depends(get_db)):
    service = ReservationService(db)
    return service.get_reservations()


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
    service = ReservationService(db)
    return service.get_reservation_by_id(reservation_id)


@router.put(
    "/{reservation_id}",
    response_model=ReservationResponse,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def update_reservation(
    reservation_id: int,
    data: ReservationUpdate,
    db: Session = Depends(get_db)
):
    """PUT /reservations/{id} (Member 1 API requirement)."""
    service = ReservationService(db)
    return service.update_reservation(reservation_id, data)


@router.delete(
    "/{reservation_id}",
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """DELETE /reservations/{id} with cancellation policy tiers (Section 28)."""
    service = ReservationService(db)
    return service.cancel_reservation(reservation_id)


@router.post(
    "/{reservation_id}/check-in",
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def check_in_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    service = CheckInService(db)
    return service.check_in_guest(reservation_id)


@router.post(
    "/{reservation_id}/check-out",
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def check_out_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """POST /reservations/{id}/check-out (PDF Page 6 API requirement)."""
    service = CheckOutService(db)
    return service.check_out_guest(reservation_id)


@router.post(
    "/no-shows/process",
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))]
)
def process_no_shows(db: Session = Depends(get_db)):
    """Automate transitioning overdue confirmed reservations to NO_SHOW (Section 28)."""
    service = ReservationService(db)
    return service.process_no_shows()
