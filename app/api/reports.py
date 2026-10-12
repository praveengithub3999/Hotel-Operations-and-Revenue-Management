
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.roles import require_role
from app.database.database import get_db
from app.models.room import Room
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.reservation import Reservation
from app.schemas.report import (
    OccupancyReport,
    RevenueReport,
    ReservationReport,
    RoomStatusReport
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


# Occupancy report: Admin and Manager
@router.get(
    "/occupancy",
    response_model=OccupancyReport,
    dependencies=[Depends(require_role("ADMIN", "MANAGER"))]
)
def get_occupancy_report(
    db: Session = Depends(get_db)
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
        Room.status.in_(["MAINTENANCE", "OUT_OF_SERVICE"])
    ).count()

    cleaning_rooms = db.query(Room).filter(
        Room.status == "CLEANING"
    ).count()

    occupancy_percentage = (
        occupied_rooms / total_rooms * 100
        if total_rooms else 0
    )

    return {
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "available_rooms": available_rooms,
        "reserved_rooms": reserved_rooms,
        "dirty_rooms": dirty_rooms,
        "maintenance_rooms": maintenance_rooms,
        "cleaning_rooms": cleaning_rooms,
        "occupancy_percentage": round(occupancy_percentage, 2)
    }


# Revenue report: Admin, Finance and Manager
@router.get(
    "/revenue",
    response_model=RevenueReport,
    dependencies=[
        Depends(require_role("ADMIN", "FINANCE", "MANAGER"))
    ]
)
def get_revenue_report(
    db: Session = Depends(get_db)
):
    total_charges = db.query(
        func.coalesce(func.sum(Charge.total_amount), 0)
    ).scalar()

    successful_payments = db.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.payment_status.in_([
            "SUCCESS",
            "PARTIALLY_REFUNDED",
            "REFUNDED"
        ])
    ).scalar()

    successful_refunds = db.query(
        func.coalesce(func.sum(Refund.amount), 0)
    ).filter(
        Refund.status == "SUCCESS"
    ).scalar()

    payment_amount = Decimal(str(successful_payments))
    refund_amount = Decimal(str(successful_refunds))

    net_revenue = payment_amount - refund_amount

    return {
        "total_charges": float(total_charges or 0),
        "successful_payments": float(payment_amount),
        "total_revenue": float(net_revenue)
    }


# Reservation report: Admin, Receptionist and Manager
@router.get(
    "/reservations",
    response_model=ReservationReport,
    dependencies=[
        Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))
    ]
)
def get_reservation_report(
    db: Session = Depends(get_db)
):
    statuses = {
        "pending": "PENDING",
        "confirmed": "CONFIRMED",
        "checked_in": "CHECKED_IN",
        "checked_out": "CHECKED_OUT",
        "cancelled": "CANCELLED",
        "no_show": "NO_SHOW"
    }

    counts = {
        key: db.query(Reservation).filter(
            Reservation.status == status
        ).count()
        for key, status in statuses.items()
    }

    counts["total_reservations"] = db.query(Reservation).count()

    return counts


# Room status report: Admin and Manager
@router.get(
    "/rooms",
    response_model=RoomStatusReport,
    dependencies=[Depends(require_role("ADMIN", "MANAGER"))]
)
def get_room_status_report(
    db: Session = Depends(get_db)
):
    statuses = {
        "available": "AVAILABLE",
        "reserved": "RESERVED",
        "occupied": "OCCUPIED",
        "dirty": "DIRTY",
        "cleaning": "CLEANING",
        "maintenance": ["MAINTENANCE", "OUT_OF_SERVICE"]
    }

    counts = {}

    for key, status in statuses.items():
        query = db.query(Room)

        if isinstance(status, list):
            query = query.filter(Room.status.in_(status))
        else:
            query = query.filter(Room.status == status)

        counts[key] = query.count()

    counts["total_rooms"] = db.query(Room).count()

    return counts
