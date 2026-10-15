from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.services.billing_service import BillingService

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
    service = BillingService(db)
    return service.create_invoice(invoice_data)


@router.get(
    "/",
    response_model=List[InvoiceResponse],
    dependencies=[Depends(require_role("ADMIN", "FINANCE", "MANAGER"))]
)
def get_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).all()


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_role("ADMIN", "FINANCE", "MANAGER"))]
)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
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
    service = BillingService(db)
    return service.recalculate_invoice(invoice_id)
