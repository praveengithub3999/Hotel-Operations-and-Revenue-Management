from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.report import (
    OccupancyReport,
    RevenueReport,
    ReservationReport,
    RoomStatusReport,
    RoomPerformanceReport
)
from app.services.revenue_service import RevenueService

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@router.get(
    "/occupancy",
    response_model=OccupancyReport,
    dependencies=[Depends(require_role("ADMIN", "MANAGER"))]
)
def get_occupancy_report(db: Session = Depends(get_db)):
    service = RevenueService(db)
    return service.get_occupancy_report()


@router.get(
    "/revenue",
    response_model=RevenueReport,
    dependencies=[Depends(require_role("ADMIN", "FINANCE", "MANAGER"))]
)
def get_revenue_report(db: Session = Depends(get_db)):
    service = RevenueService(db)
    return service.get_revenue_report()


@router.get(
    "/room-performance",
    response_model=RoomPerformanceReport,
    dependencies=[Depends(require_role("ADMIN", "MANAGER", "FINANCE"))]
)
def get_room_performance_report(db: Session = Depends(get_db)):
    """GET /reports/room-performance (PDF Page 10 & 24 API requirement)."""
    service = RevenueService(db)
    return service.get_room_performance_report()


@router.get(
    "/reservations",
    response_model=ReservationReport,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))]
)
def get_reservation_report(db: Session = Depends(get_db)):
    service = RevenueService(db)
    return service.get_reservation_report()


@router.get(
    "/rooms",
    response_model=RoomStatusReport,
    dependencies=[Depends(require_role("ADMIN", "MANAGER"))]
)
def get_room_status_report(db: Session = Depends(get_db)):
    service = RevenueService(db)
    return service.get_room_status_report()
