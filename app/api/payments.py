from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.refund import Refund
from app.schemas.payment import PaymentCreate, PaymentResponse

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
    try:
        # Lock the invoice while checking and recording the payment.
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == payment_data.invoice_id)
            .with_for_update()
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )

        if invoice.status not in ["UNPAID", "PARTIALLY_PAID"]:
            raise HTTPException(
                status_code=400,
                detail="Payments are not allowed for this invoice status"
            )

        existing_payments = db.query(Payment).filter(
            Payment.invoice_id == invoice.id
        ).with_for_update().all()

        successful_payments = [
            payment for payment in existing_payments
            if payment.payment_status in [
                "SUCCESS",
                "PARTIALLY_REFUNDED",
                "REFUNDED"
            ]
        ]

        gross_paid = sum(
            (payment.amount for payment in successful_payments),
            Decimal("0.00")
        )

        successful_refunds = db.query(Refund).join(
            Payment,
            Refund.payment_id == Payment.id
        ).filter(
            Payment.invoice_id == invoice.id,
            Refund.status == "SUCCESS"
        ).all()

        refunded_amount = sum(
            (refund.amount for refund in successful_refunds),
            Decimal("0.00")
        )

        net_paid = gross_paid - refunded_amount
        remaining_amount = invoice.total - net_paid

        if remaining_amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invoice has no remaining balance"
            )

        if payment_data.amount > remaining_amount:
            raise HTTPException(
                status_code=400,
                detail="Payment amount exceeds the remaining invoice balance"
            )

        payment = Payment(
            invoice_id=invoice.id,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            payment_status="SUCCESS",
            transaction_reference=payment_data.transaction_reference
        )

        db.add(payment)
        db.flush()

        new_net_paid = net_paid + payment_data.amount

        if new_net_paid == invoice.total:
            invoice.status = "PAID"
        else:
            invoice.status = "PARTIALLY_PAID"

        db.commit()
        db.refresh(payment)

        return payment

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
