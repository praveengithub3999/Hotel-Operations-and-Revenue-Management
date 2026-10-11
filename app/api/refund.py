from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from app.models.invoice import Invoice
from app.database.database import get_db
from app.models.payment import Payment
from app.schemas.refund import RefundCreate
from app.models.refund import Refund

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
    ).with_for_update().first()

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

    # Calculate the amount already refunded.
    previous_refunds = db.query(Refund).filter(
        Refund.payment_id == payment.id,
        Refund.status == "SUCCESS"
    ).all()

    already_refunded = sum(
        (refund.amount for refund in previous_refunds),
        Decimal("0.00")
    )

    remaining_amount = payment.amount - already_refunded

    if refund_data.amount > remaining_amount:
        raise HTTPException(
            status_code=400,
            detail="Refund amount exceeds the remaining refundable amount"
        )

    # Save this refund in the database.
    new_refund = Refund(
        payment_id=payment.id,
        amount=refund_data.amount,
        status="SUCCESS"
    )
    db.add(new_refund)

    total_refunded = already_refunded + refund_data.amount

    if total_refunded == payment.amount:
        payment.payment_status = "REFUNDED"
    else:
        payment.payment_status = "PARTIALLY_REFUNDED"

    invoice = db.query(Invoice).filter(
        Invoice.id == payment.invoice_id
    ).first()

    if not invoice:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    # Update invoice only when all payments for it
    # have been fully refunded.
    invoice_payments = db.query(Payment).filter(
        Payment.invoice_id == invoice.id
    ).all()

    all_payments_refunded = all(
        p.payment_status == "REFUNDED"
        for p in invoice_payments
    )

    if all_payments_refunded:
        invoice.status = "REFUNDED"

    try:
        db.commit()
        db.refresh(new_refund)
        db.refresh(payment)
        db.refresh(invoice)
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Refund processed successfully",
        "refund_id": new_refund.id,
        "payment_id": payment.id,
        "refund_amount": str(new_refund.amount),
        "total_refunded": str(total_refunded),
        "payment_status": payment.payment_status,
        "invoice_status": invoice.status
    }
