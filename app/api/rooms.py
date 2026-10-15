from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse
from app.services.room_service import RoomService

router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)


@router.post(
    "/",
    response_model=RoomResponse,
    dependencies=[Depends(require_role("ADMIN"))]
)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db)
):
    service = RoomService(db)
    return service.create_room(room)


@router.get(
    "/",
    response_model=List[RoomResponse],
    dependencies=[
        Depends(require_role(
            "ADMIN",
            "RECEPTIONIST",
            "HOUSEKEEPING",
            "MAINTENANCE",
            "MANAGER"
        ))
    ]
)
def get_rooms(db: Session = Depends(get_db)):
    service = RoomService(db)
    return service.get_rooms()


@router.get(
    "/availability",
    response_model=List[RoomResponse],
    dependencies=[
        Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))
    ]
)
def get_available_rooms(
    check_in_date: date = Query(..., description="Target check-in date"),
    check_out_date: date = Query(..., description="Target check-out date"),
    hotel_id: Optional[int] = Query(None, description="Optional hotel filter"),
    room_type_id: Optional[int] = Query(None, description="Optional room type filter"),
    db: Session = Depends(get_db)
):
    """GET /rooms/availability (Member 1 API requirement)."""
    service = RoomService(db)
    return service.get_available_rooms(
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        hotel_id=hotel_id,
        room_type_id=room_type_id
    )


@router.get(
    "/{room_id}",
    response_model=RoomResponse,
    dependencies=[
        Depends(require_role(
            "ADMIN",
            "RECEPTIONIST",
            "HOUSEKEEPING",
            "MAINTENANCE",
            "MANAGER"
        ))
    ]
)
def get_room(
    room_id: int,
    db: Session = Depends(get_db)
):
    service = RoomService(db)
    return service.get_room_by_id(room_id)


@router.put(
    "/{room_id}",
    response_model=RoomResponse,
    dependencies=[Depends(require_role("ADMIN"))]
)
def update_room(
    room_id: int,
    data: RoomUpdate,
    db: Session = Depends(get_db)
):
    """PUT /rooms/{id} (Member 1 API requirement)."""
    service = RoomService(db)
    return service.update_room(room_id, data)


@router.get(
    "/{room_id}/pricing",
    dependencies=[
        Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))
    ]
)
def get_room_dynamic_price(
    room_id: int,
    stay_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db)
):
    """Calculate dynamic room price based on weekdays, weekends, and season (Section 28)."""
    service = RoomService(db)
    room = service.get_room_by_id(room_id)
    price = service.calculate_dynamic_price(room.room_type_id, stay_date)
    return {
        "room_id": room.id,
        "room_number": room.room_number,
        "stay_date": str(stay_date),
        "is_weekend": stay_date.weekday() in (4, 5),
        "is_peak_month": stay_date.month in (10, 12),
        "dynamic_price": str(price)
    }
