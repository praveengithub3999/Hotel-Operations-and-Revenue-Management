from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.discount import DiscountCreate, DiscountResponse
from app.services.billing_service import BillingService

router = APIRouter(
    prefix="/discounts",
    tags=["Discounts"]
)


@router.post(
    "/",
    response_model=DiscountResponse,
    dependencies=[Depends(require_role("ADMIN", "FINANCE"))]
)
def create_discount(
    data: DiscountCreate,
    db: Session = Depends(get_db)
):
    """POST /discounts (Member 3 API requirement)."""
    service = BillingService(db)
    return service.create_discount(data)


@router.get(
    "/",
    response_model=List[DiscountResponse],
    dependencies=[Depends(require_role("ADMIN", "FINANCE", "RECEPTIONIST", "MANAGER"))]
)
def get_discounts(db: Session = Depends(get_db)):
    service = BillingService(db)
    return service.get_discounts()
