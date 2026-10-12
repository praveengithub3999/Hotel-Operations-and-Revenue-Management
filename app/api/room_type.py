from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.roles import require_role
from app.database.database import get_db
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.schemas.room_type import RoomTypeCreate, RoomTypeResponse

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
    try:
        hotel = db.query(Hotel).filter(
            Hotel.id == room_type.hotel_id
        ).first()

        if not hotel:
            raise HTTPException(
                status_code=404,
                detail="Hotel not found"
            )

        existing_type = db.query(RoomType).filter(
            RoomType.hotel_id == room_type.hotel_id,
            func.lower(RoomType.name) == room_type.name.lower()
        ).first()

        if existing_type:
            raise HTTPException(
                status_code=409,
                detail="This room type already exists for this hotel"
            )

        new_room_type = RoomType(
            hotel_id=room_type.hotel_id,
            name=room_type.name,
            description=room_type.description,
            capacity=room_type.capacity,
            base_price=room_type.base_price
        )

        db.add(new_room_type)
        db.commit()
        db.refresh(new_room_type)

        return new_room_type

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get(
    "/",
    response_model=list[RoomTypeResponse],
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
    return db.query(RoomType).all()


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
    room_type = db.query(RoomType).filter(
        RoomType.id == room_type_id
    ).first()

    if not room_type:
        raise HTTPException(
            status_code=404,
            detail="Room type not found"
        )

    return room_type
