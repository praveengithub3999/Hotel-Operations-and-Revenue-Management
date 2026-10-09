from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.models.room import Room
from app.schemas.room import RoomCreate, RoomResponse


router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)


@router.post("/", response_model=RoomResponse)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(
        Hotel.id == room.hotel_id
    ).first()

    if not hotel:
        raise HTTPException(
            status_code=404,
            detail="Hotel not found"
        )

    room_type = db.query(RoomType).filter(
        RoomType.id == room.room_type_id
    ).first()

    if not room_type:
        raise HTTPException(
            status_code=404,
            detail="Room type not found"
        )

    existing_room = db.query(Room).filter(
        Room.room_number == room.room_number
    ).first()

    if existing_room:
        raise HTTPException(
            status_code=400,
            detail="Room number already exists"
        )

    new_room = Room(
        hotel_id=room.hotel_id,
        room_type_id=room.room_type_id,
        room_number=room.room_number,
        floor=room.floor
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return new_room


@router.get("/", response_model=list[RoomResponse])
def get_rooms(
    db: Session = Depends(get_db)
):
    return db.query(Room).all()


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(
        Room.id == room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    return room