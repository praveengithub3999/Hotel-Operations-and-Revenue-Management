
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.models.hotel import Hotel
from app.schemas.hotel import HotelCreate, HotelResponse
from app.core.roles import require_role


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
    try:
        # Check for a hotel with the same name in the same city
        existing_hotel = db.query(Hotel).filter(
            func.lower(Hotel.name) == hotel.name.strip().lower(),
            func.lower(Hotel.city) == hotel.city.strip().lower()
        ).first()

        if existing_hotel:
            raise HTTPException(
                status_code=409,
                detail="A hotel with this name already exists in this city"
            )

        new_hotel = Hotel(
            name=hotel.name.strip(),
            address=hotel.address.strip(),
            city=hotel.city.strip(),
            contact_number=hotel.contact_number.strip()
        )

        db.add(new_hotel)
        db.commit()
        db.refresh(new_hotel)

        return new_hotel

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


@router.get(
    "/",
    response_model=list[HotelResponse],
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
    return db.query(Hotel).order_by(Hotel.id).all()


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
    if hotel_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Hotel ID must be greater than zero"
        )

    hotel = db.query(Hotel).filter(
        Hotel.id == hotel_id
    ).first()

    if not hotel:
        raise HTTPException(
            status_code=404,
            detail="Hotel not found"
        )

    return hotel
