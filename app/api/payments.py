from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.schemas.payment import PaymentCreate, PaymentResponse


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    # Check invoice
    invoice = db.query(Invoice).filter(
        Invoice.id == payment_data.invoice_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    # Check payment amount
    if payment_data.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero"
        )

    # Check payment method
    allowed_methods = [
        "CASH",
        "CARD",
        "UPI",
        "BANK_TRANSFER"
    ]

    if payment_data.payment_method not in allowed_methods:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment method"
        )

    # Check if invoice is already fully paid
    existing_payments = db.query(Payment).filter(
        Payment.invoice_id == payment_data.invoice_id,
        Payment.payment_status == "SUCCESS"
    ).all()

    paid_amount = sum(
        (payment.amount for payment in existing_payments),
        start=0
    )

    if paid_amount + payment_data.amount > invoice.total:
        raise HTTPException(
            status_code=400,
            detail="Payment amount exceeds invoice total"
        )

    payment = Payment(
        invoice_id=payment_data.invoice_id,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        payment_status="SUCCESS",
        transaction_reference=payment_data.transaction_reference
    )

    db.add(payment)

    # Update invoice status
    if paid_amount + payment_data.amount == invoice.total:
        invoice.status = "PAID"

    db.commit()
    db.refresh(payment)

    return payment