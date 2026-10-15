from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.hotel import HotelCreate, HotelResponse
from app.core.roles import require_role
from app.services.hotel_service import HotelService

router = APIRouter(
    prefix="/hotels",
    tags=["Hotels"]
)


@router.post(
    "/",
    response_model=HotelResponse,
    dependencies=[Depends(require_role("ADMIN"))]
)
def create_hotel(
    hotel: HotelCreate,
    db: Session = Depends(get_db)
):
    service = HotelService(db)
    return service.create_hotel(hotel)


@router.get(
    "/",
    response_model=List[HotelResponse],
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
def get_hotels(
    db: Session = Depends(get_db)
):
    service = HotelService(db)
    return service.get_hotels()


@router.get(
    "/{hotel_id}",
    response_model=HotelResponse,
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
def get_hotel(
    hotel_id: int,
    db: Session = Depends(get_db)
):
    service = HotelService(db)
    return service.get_hotel_by_id(hotel_id)
