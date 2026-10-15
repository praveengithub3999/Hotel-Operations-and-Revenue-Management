from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.refund import RefundCreate
from app.services.payment_service import PaymentService

router = APIRouter(
    prefix="/refunds",
    tags=["Refunds"]
)


@router.post(
    "/",
    dependencies=[Depends(require_role("ADMIN", "FINANCE"))]
)
def create_refund(
    refund_data: RefundCreate,
    db: Session = Depends(get_db)
):
    service = PaymentService(db)
    return service.create_refund(refund_data)
