from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.hotel import Hotel
from app.schemas.hotel import HotelCreate, HotelResponse
from fastapi import Depends
from app.core.dependencies import get_current_user
from app.core.roles import require_role


router = APIRouter(
    prefix="/hotels",
    tags=["Hotels"]
)


@router.post("/", response_model=HotelResponse)
def create_hotel(
    hotel: HotelCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN"))
):
    new_hotel = Hotel(
        name=hotel.name,
        address=hotel.address,
        city=hotel.city,
        contact_number=hotel.contact_number
    )

    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)

    return new_hotel


@router.get("/", response_model=list[HotelResponse])
def get_hotels(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    hotels = db.query(Hotel).all()

    return hotels


@router.get("/{hotel_id}", response_model=HotelResponse)
def get_hotel(
    hotel_id: int,
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(
        Hotel.id == hotel_id
    ).first()

    if not hotel:
        raise HTTPException(
            status_code=404,
            detail="Hotel not found"
        )

    return hotel