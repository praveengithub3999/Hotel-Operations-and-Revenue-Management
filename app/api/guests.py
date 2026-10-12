from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.guest import Guest
from app.schemas.guest import GuestCreate, GuestResponse

router = APIRouter(
    prefix="/guests",
    tags=["Guests"]
)


@router.post(
    "/",
    response_model=GuestResponse,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def create_guest(
    guest: GuestCreate,
    db: Session = Depends(get_db)
):
    try:
        if guest.email:
            existing_email = db.query(Guest).filter(
                Guest.email == guest.email
            ).first()

            if existing_email:
                raise HTTPException(
                    status_code=409,
                    detail="A guest with this email already exists"
                )

        if guest.id_reference:
            existing_id = db.query(Guest).filter(
                Guest.id_reference == guest.id_reference
            ).first()

            if existing_id:
                raise HTTPException(
                    status_code=409,
                    detail="A guest with this ID reference already exists"
                )

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

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get(
    "/",
    response_model=list[GuestResponse],
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))]
)
def get_guests(db: Session = Depends(get_db)):
    return db.query(Guest).all()


@router.get(
    "/{guest_id}",
    response_model=GuestResponse,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))]
)
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
