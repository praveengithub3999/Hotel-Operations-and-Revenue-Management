from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from app.models.room import Room
from app.core.dependencies import get_current_user
from app.schemas.report import OccupancyReport, RevenueReport, ReservationReport, RoomStatusReport
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.reservation import Reservation

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@router.get(
    "/occupancy",
    response_model=OccupancyReport
)
def get_occupancy_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    total_rooms = db.query(Room).count()

    occupied_rooms = db.query(Room).filter(
        Room.status == "OCCUPIED"
    ).count()

    available_rooms = db.query(Room).filter(
        Room.status == "AVAILABLE"
    ).count()

    reserved_rooms = db.query(Room).filter(
        Room.status == "RESERVED"
    ).count()

    dirty_rooms = db.query(Room).filter(
        Room.status == "DIRTY"
    ).count()

    maintenance_rooms = db.query(Room).filter(
        Room.status == "MAINTENANCE"
    ).count()

    if total_rooms > 0:
        occupancy_percentage = (
            occupied_rooms / total_rooms
        ) * 100
    else:
        occupancy_percentage = 0

    return {
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "available_rooms": available_rooms,
        "reserved_rooms": reserved_rooms,
        "dirty_rooms": dirty_rooms,
        "maintenance_rooms": maintenance_rooms,
        "occupancy_percentage": round(
            occupancy_percentage, 2
        )
    }

@router.get(
    "/revenue",
    response_model=RevenueReport
)
def get_revenue_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    total_charges = db.query(
        func.coalesce(func.sum(Charge.total_amount), 0)
    ).scalar()

    successful_payments = db.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.payment_status == "SUCCESS"
    ).scalar()

    total_revenue = successful_payments

    return {
        "total_charges": float(total_charges),
        "successful_payments": float(successful_payments),
        "total_revenue": float(total_revenue)
    }

@router.get(
    "/reservations",
    response_model=ReservationReport
)
def get_reservation_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    pending = db.query(Reservation).filter(
        Reservation.status == "PENDING"
    ).count()

    confirmed = db.query(Reservation).filter(
        Reservation.status == "CONFIRMED"
    ).count()

    checked_in = db.query(Reservation).filter(
        Reservation.status == "CHECKED_IN"
    ).count()

    checked_out = db.query(Reservation).filter(
        Reservation.status == "CHECKED_OUT"
    ).count()

    cancelled = db.query(Reservation).filter(
        Reservation.status == "CANCELLED"
    ).count()

    no_show = db.query(Reservation).filter(
        Reservation.status == "NO_SHOW"
    ).count()

    total_reservations = db.query(Reservation).count()

    return {
        "pending": pending,
        "confirmed": confirmed,
        "checked_in": checked_in,
        "checked_out": checked_out,
        "cancelled": cancelled,
        "no_show": no_show,
        "total_reservations": total_reservations
    }

@router.get(
    "/rooms",
    response_model=RoomStatusReport
)
def get_room_status_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    available = db.query(Room).filter(
        Room.status == "AVAILABLE"
    ).count()

    reserved = db.query(Room).filter(
        Room.status == "RESERVED"
    ).count()

    occupied = db.query(Room).filter(
        Room.status == "OCCUPIED"
    ).count()

    dirty = db.query(Room).filter(
        Room.status == "DIRTY"
    ).count()

    cleaning = db.query(Room).filter(
        Room.status == "CLEANING"
    ).count()

    maintenance = db.query(Room).filter(
        Room.status == "MAINTENANCE"
    ).count()

    total_rooms = db.query(Room).count()

    return {
        "available": available,
        "reserved": reserved,
        "occupied": occupied,
        "dirty": dirty,
        "cleaning": cleaning,
        "maintenance": maintenance,
        "total_rooms": total_rooms
    }