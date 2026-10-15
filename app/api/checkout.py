from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.services.check_out_service import CheckOutService

router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"]
)


@router.post(
    "/{reservation_id}",
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def checkout(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    service = CheckOutService(db)
    return service.check_out_guest(reservation_id)
