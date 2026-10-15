from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.guest import GuestCreate, GuestResponse
from app.services.guest_service import GuestService

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
    service = GuestService(db)
    return service.create_guest(guest)


@router.get(
    "/",
    response_model=List[GuestResponse],
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))]
)
def get_guests(db: Session = Depends(get_db)):
    service = GuestService(db)
    return service.get_guests()


@router.get(
    "/{guest_id}",
    response_model=GuestResponse,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))]
)
def get_guest(
    guest_id: int,
    db: Session = Depends(get_db)
):
    service = GuestService(db)
    return service.get_guest_by_id(guest_id)
