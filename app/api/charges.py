from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.charge import ChargeCreate, ChargeResponse
from app.services.billing_service import BillingService

router = APIRouter(
    prefix="/charges",
    tags=["Charges"]
)


@router.post(
    "/",
    response_model=ChargeResponse,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def create_charge(
    charge: ChargeCreate,
    allow_duplicate: bool = Query(False, description="Bypass duplicate charge check"),
    db: Session = Depends(get_db)
):
    service = BillingService(db)
    return service.add_charge(charge, allow_duplicate=allow_duplicate)


@router.post(
    "/calculate-room/{reservation_id}",
    response_model=ChargeResponse,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def calculate_room_charges(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """Auto-calculate and attach room stay charge (room price * nights)."""
    service = BillingService(db)
    return service.calculate_room_charges(reservation_id)


@router.get(
    "/{reservation_id}",
    response_model=List[ChargeResponse],
    dependencies=[
        Depends(
            require_role(
                "ADMIN",
                "RECEPTIONIST",
                "FINANCE",
                "MANAGER"
            )
        )
    ]
)
def get_charges(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    service = BillingService(db)
    return service.get_charges(reservation_id)
