from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database.database import get_db
from app.models.payment import Payment
from app.schemas.refund import RefundCreate


router = APIRouter(
    prefix="/refunds",
    tags=["Refunds"]
)


@router.post("/")
def create_refund(
    refund_data: RefundCreate,
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(
        Payment.id == refund_data.payment_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    if payment.payment_status not in [
        "SUCCESS",
        "PARTIALLY_REFUNDED"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Payment cannot be refunded"
        )

    if refund_data.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Refund amount must be greater than zero"
        )

    if refund_data.amount > payment.amount:
        raise HTTPException(
            status_code=400,
            detail="Refund amount cannot exceed payment amount"
        )

    if refund_data.amount == payment.amount:
        payment.payment_status = "REFUNDED"
    else:
        payment.payment_status = "PARTIALLY_REFUNDED"

    db.commit()
    db.refresh(payment)

    return {
        "message": "Refund processed successfully",
        "payment_id": payment.id,
        "refund_amount": refund_data.amount,
        "payment_status": payment.payment_status
    }