from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.invoice import Invoice
from app.models.reservation import Reservation
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.refund import Refund
from app.schemas.invoice import InvoiceCreate, InvoiceResponse

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)


@router.post(
    "/",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_role("ADMIN", "FINANCE"))]
)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    try:
        reservation = db.query(Reservation).filter(
            Reservation.id == invoice_data.reservation_id
        ).with_for_update().first()

        if not reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )

        existing_invoice = db.query(Invoice).filter(
            Invoice.reservation_id == invoice_data.reservation_id
        ).first()

        if existing_invoice:
            raise HTTPException(
                status_code=400,
                detail="Invoice already exists for this reservation"
            )

        if invoice_data.discount < 0:
            raise HTTPException(
                status_code=400,
                detail="Discount cannot be negative"
            )

        if not Decimal("0") <= invoice_data.tax_percentage <= Decimal("100"):
            raise HTTPException(
                status_code=400,
                detail="Tax percentage must be between 0 and 100"
            )

        charges = db.query(Charge).filter(
            Charge.reservation_id == invoice_data.reservation_id
        ).all()

        subtotal = sum(
            (charge.total_amount for charge in charges),
            Decimal("0.00")
        )

        if invoice_data.discount > subtotal:
            raise HTTPException(
                status_code=400,
                detail="Discount cannot be greater than subtotal"
            )

        taxable_amount = subtotal - invoice_data.discount
        tax = taxable_amount * invoice_data.tax_percentage / Decimal("100")
        total = taxable_amount + tax

        new_invoice = Invoice(
            reservation_id=invoice_data.reservation_id,
            subtotal=subtotal,
            discount=invoice_data.discount,
            tax_percentage=invoice_data.tax_percentage,
            tax=tax,
            total=total,
            status="UNPAID"
        )

        db.add(new_invoice)
        db.commit()
        db.refresh(new_invoice)

        return new_invoice

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get(
    "/",
    response_model=list[InvoiceResponse],
    dependencies=[
        Depends(require_role("ADMIN", "FINANCE", "RECEPTIONIST", "MANAGER"))
    ]
)
def get_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).all()


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    dependencies=[
        Depends(require_role("ADMIN", "FINANCE", "RECEPTIONIST", "MANAGER"))
    ]
)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    return invoice


@router.post(
    "/{invoice_id}/recalculate",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_role("ADMIN", "FINANCE"))]
)
def recalculate_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    try:
        invoice = db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).with_for_update().first()

        if not invoice:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found"
            )

        if invoice.status != "UNPAID":
            raise HTTPException(
                status_code=400,
                detail="Only unpaid invoices can be recalculated"
            )

        existing_payments = db.query(Payment).filter(
            Payment.invoice_id == invoice.id
        ).all()

        if existing_payments:
            raise HTTPException(
                status_code=400,
                detail="Invoices with payment records cannot be recalculated"
            )

        charges = db.query(Charge).filter(
            Charge.reservation_id == invoice.reservation_id
        ).all()

        subtotal = sum(
            (charge.total_amount for charge in charges),
            Decimal("0.00")
        )

        if invoice.discount > subtotal:
            raise HTTPException(
                status_code=400,
                detail="Existing discount cannot be greater than subtotal"
            )

        taxable_amount = subtotal - invoice.discount
        tax = taxable_amount * invoice.tax_percentage / Decimal("100")
        total = taxable_amount + tax

        invoice.subtotal = subtotal
        invoice.tax = tax
        invoice.total = total

        db.commit()
        db.refresh(invoice)

        return invoice

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
