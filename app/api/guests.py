from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.guest import Guest
from app.schemas.guest import GuestCreate, GuestResponse


router = APIRouter(
    prefix="/guests",
    tags=["Guests"]
)


@router.post("/", response_model=GuestResponse)
def create_guest(
    guest: GuestCreate,
    db: Session = Depends(get_db)
):
    new_guest = Guest(
        first_name=guest.first_name,
        last_name=guest.last_name,
        email=guest.email,
        phone=guest.phone,
        address=guest.address,
        id_type=guest.id_type,
        id_reference=guest.id_reference
    )

    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)

    return new_guest


@router.get("/", response_model=list[GuestResponse])
def get_guests(
    db: Session = Depends(get_db)
):
    return db.query(Guest).all()


@router.get("/{guest_id}", response_model=GuestResponse)
def get_guest(
    guest_id: int,
    db: Session = Depends(get_db)
):
    guest = db.query(Guest).filter(
        Guest.id == guest_id
    ).first()

    if not guest:
        raise HTTPException(
            status_code=404,
            detail="Guest not found"
        )

    return guest