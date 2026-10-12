from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.refund import Refund
from app.schemas.refund import RefundCreate

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
    try:
        # Find the payment first to identify its invoice.
        payment = db.query(Payment).filter(
            Payment.id == refund_data.payment_id
        ).first()

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found"
            )

        # Lock the invoice first to coordinate payment/refund operations.
        invoice = db.query(Invoice).filter(
            Invoice.id == payment.invoice_id
        ).with_for_update().first()

        if not invoice:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )

        # Lock and re-fetch the payment after acquiring the invoice lock.
        payment = db.query(Payment).filter(
            Payment.id == refund_data.payment_id
        ).with_for_update().first()

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

        previous_refunds = db.query(Refund).filter(
            Refund.payment_id == payment.id,
            Refund.status == "SUCCESS"
        ).all()

        already_refunded = sum(
            (refund.amount for refund in previous_refunds),
            Decimal("0.00")
        )

        remaining_refundable = payment.amount - already_refunded

        if refund_data.amount > remaining_refundable:
            raise HTTPException(
                status_code=400,
                detail="Refund amount exceeds the remaining refundable amount"
            )

        new_refund = Refund(
            payment_id=payment.id,
            amount=refund_data.amount,
            status="SUCCESS"
        )
        db.add(new_refund)
        db.flush()

        total_refunded_for_payment = (
            already_refunded + refund_data.amount
        )

        if total_refunded_for_payment == payment.amount:
            payment.payment_status = "REFUNDED"
        else:
            payment.payment_status = "PARTIALLY_REFUNDED"

        # Calculate the invoice's remaining net amount paid.
        invoice_payments = db.query(Payment).filter(
            Payment.invoice_id == invoice.id
        ).with_for_update().all()

        gross_paid = sum(
            (
                p.amount for p in invoice_payments
                if p.payment_status in [
                    "SUCCESS",
                    "PARTIALLY_REFUNDED",
                    "REFUNDED"
                ]
            ),
            Decimal("0.00")
        )

        all_successful_refunds = db.query(Refund).join(
            Payment,
            Refund.payment_id == Payment.id
        ).filter(
            Payment.invoice_id == invoice.id,
            Refund.status == "SUCCESS"
        ).all()

        total_refunded = sum(
            (refund.amount for refund in all_successful_refunds),
            Decimal("0.00")
        )

        net_paid = gross_paid - total_refunded

        if net_paid <= 0 and total_refunded > 0:
            invoice.status = "REFUNDED"
        elif net_paid >= invoice.total:
            invoice.status = "PAID"
        elif net_paid > 0:
            invoice.status = "PARTIALLY_PAID"
        else:
            invoice.status = "UNPAID"

        db.commit()
        db.refresh(new_refund)
        db.refresh(payment)
        db.refresh(invoice)

        return {
            "message": "Refund processed successfully",
            "refund_id": new_refund.id,
            "payment_id": payment.id,
            "refund_amount": str(new_refund.amount),
            "total_refunded": str(total_refunded_for_payment),
            "payment_status": payment.payment_status,
            "invoice_status": invoice.status
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
