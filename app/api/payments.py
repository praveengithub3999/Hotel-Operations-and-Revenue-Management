from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post(
    "/",
    response_model=PaymentResponse,
    dependencies=[Depends(require_role("ADMIN", "FINANCE"))]
)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    service = PaymentService(db)
    return service.create_payment(payment_data)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    dependencies=[Depends(require_role("ADMIN", "FINANCE", "MANAGER"))]
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """GET /payments/{id} (PDF Page 10 API requirement)."""
    service = PaymentService(db)
    return service.get_payment_by_id(payment_id)
