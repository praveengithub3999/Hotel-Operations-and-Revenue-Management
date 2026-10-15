from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.room_type import RoomTypeCreate, RoomTypeResponse
from app.services.hotel_service import HotelService

router = APIRouter(
    prefix="/room-types",
    tags=["Room Types"]
)


@router.post(
    "/",
    response_model=RoomTypeResponse,
    dependencies=[Depends(require_role("ADMIN"))]
)
def create_room_type(
    room_type: RoomTypeCreate,
    db: Session = Depends(get_db)
):
    service = HotelService(db)
    return service.create_room_type(room_type)


@router.get(
    "/",
    response_model=List[RoomTypeResponse],
    dependencies=[
        Depends(require_role(
            "ADMIN",
            "RECEPTIONIST",
            "HOUSEKEEPING",
            "MAINTENANCE",
            "FINANCE",
            "MANAGER"
        ))
    ]
)
def get_room_types(db: Session = Depends(get_db)):
    service = HotelService(db)
    return service.get_room_types()


@router.get(
    "/{room_type_id}",
    response_model=RoomTypeResponse,
    dependencies=[
        Depends(require_role(
            "ADMIN",
            "RECEPTIONIST",
            "HOUSEKEEPING",
            "MAINTENANCE",
            "FINANCE",
            "MANAGER"
        ))
    ]
)
def get_room_type(
    room_type_id: int,
    db: Session = Depends(get_db)
):
    service = HotelService(db)
    return service.get_room_type_by_id(room_type_id)
