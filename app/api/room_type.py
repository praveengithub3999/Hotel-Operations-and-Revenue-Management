from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.schemas.room_type import RoomTypeCreate, RoomTypeResponse


router = APIRouter(
    prefix="/room-types",
    tags=["Room Types"]
)


@router.post("/", response_model=RoomTypeResponse)
def create_room_type(
    room_type: RoomTypeCreate,
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(
        Hotel.id == room_type.hotel_id
    ).first()

    if not hotel:
        raise HTTPException(
            status_code=404,
            detail="Hotel not found"
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


@router.get("/", response_model=list[RoomTypeResponse])
def get_room_types(
    db: Session = Depends(get_db)
):
    return db.query(RoomType).all()


@router.get("/{room_type_id}", response_model=RoomTypeResponse)
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