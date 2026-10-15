from decimal import Decimal
from typing import Any, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.refund import Refund
from app.repositories.billing_repository import InvoiceRepository, PaymentRepository, RefundRepository
from app.schemas.payment import PaymentCreate
from app.schemas.refund import RefundCreate
from app.utils.audit_logger import create_audit_log


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.invoice_repo = InvoiceRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.refund_repo = RefundRepository(db)

    def create_payment(self, data: PaymentCreate) -> Payment:
        invoice = self.invoice_repo.get_by_id(data.invoice_id, for_update=True)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if invoice.status not in ["UNPAID", "PARTIALLY_PAID"]:
            raise HTTPException(
                status_code=400,
                detail="Payments are not allowed for this invoice status"
            )

        existing_payments = self.payment_repo.get_by_invoice(invoice.id, for_update=True)
        successful_payments = [
            p for p in existing_payments
            if p.payment_status in ["SUCCESS", "PARTIALLY_REFUNDED", "REFUNDED"]
        ]
        gross_paid = sum((p.amount for p in successful_payments), Decimal("0.00"))

        successful_refunds = self.refund_repo.get_successful_for_invoice(invoice.id)
        refunded_amount = sum((r.amount for r in successful_refunds), Decimal("0.00"))

        net_paid = gross_paid - refunded_amount
        remaining_amount = invoice.total - net_paid

        if remaining_amount <= 0:
            raise HTTPException(status_code=400, detail="Invoice has no remaining balance")

        if data.amount > remaining_amount:
            raise HTTPException(
                status_code=400,
                detail="Payment amount exceeds the remaining invoice balance"
            )

        payment = Payment(
            invoice_id=invoice.id,
            amount=data.amount,
            payment_method=data.payment_method,
            payment_status="SUCCESS",
            transaction_reference=data.transaction_reference
        )
        self.db.add(payment)
        self.db.flush()

        new_net_paid = net_paid + data.amount
        if new_net_paid == invoice.total:
            invoice.status = "PAID"
        else:
            invoice.status = "PARTIALLY_PAID"

        self.db.commit()
        self.db.refresh(payment)

        create_audit_log(
            action="PAYMENT_RECEIVED",
            message=f"Payment of {data.amount} received via {data.payment_method}",
            reservation_id=invoice.reservation_id,
            entity="payment",
            entity_id=payment.id,
            details={"invoice_id": invoice.id, "amount": str(data.amount), "method": data.payment_method}
        )
        return payment

    def get_payment_by_id(self, payment_id: int) -> Payment:
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment

    def create_refund(self, data: RefundCreate) -> Dict[str, Any]:
        payment = self.payment_repo.get_by_id(data.payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        invoice = self.invoice_repo.get_by_id(payment.invoice_id, for_update=True)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        payment = self.payment_repo.get_by_id(data.payment_id, for_update=True)
        if payment.payment_status not in ["SUCCESS", "PARTIALLY_REFUNDED"]:
            raise HTTPException(status_code=400, detail="Payment cannot be refunded")

        if data.amount <= 0:
            raise HTTPException(status_code=400, detail="Refund amount must be greater than zero")

        previous_refunds = self.refund_repo.get_by_payment(payment.id)
        already_refunded = sum(
            (r.amount for r in previous_refunds if r.status == "SUCCESS"),
            Decimal("0.00")
        )
        remaining_refundable = payment.amount - already_refunded

        if data.amount > remaining_refundable:
            raise HTTPException(
                status_code=400,
                detail="Refund amount exceeds the remaining refundable amount"
            )

        refund = Refund(
            payment_id=payment.id,
            amount=data.amount,
            status="SUCCESS"
        )
        self.db.add(refund)
        self.db.flush()

        total_refunded_for_payment = already_refunded + data.amount
        if total_refunded_for_payment == payment.amount:
            payment.payment_status = "REFUNDED"
        else:
            payment.payment_status = "PARTIALLY_REFUNDED"

        # Calculate invoice net paid
        invoice_payments = self.payment_repo.get_by_invoice(invoice.id, for_update=True)
        gross_paid = sum(
            (
                p.amount for p in invoice_payments
                if p.payment_status in ["SUCCESS", "PARTIALLY_REFUNDED", "REFUNDED"]
            ),
            Decimal("0.00")
        )
        all_refunds = self.refund_repo.get_successful_for_invoice(invoice.id)
        total_refunded = sum((r.amount for r in all_refunds), Decimal("0.00"))
        net_paid = gross_paid - total_refunded

        if net_paid <= 0 and total_refunded > 0:
            invoice.status = "REFUNDED"
        elif net_paid >= invoice.total:
            invoice.status = "PAID"
        elif net_paid > 0:
            invoice.status = "PARTIALLY_PAID"
        else:
            invoice.status = "UNPAID"

        self.db.commit()
        self.db.refresh(refund)
        self.db.refresh(payment)
        self.db.refresh(invoice)

        create_audit_log(
            action="REFUND_PROCESSED",
            message=f"Refund of {data.amount} processed for payment {payment.id}",
            reservation_id=invoice.reservation_id,
            entity="refund",
            entity_id=refund.id,
            details={"invoice_id": invoice.id, "amount": str(data.amount)}
        )

        return {
            "message": "Refund processed successfully",
            "refund_id": refund.id,
            "payment_id": payment.id,
            "refund_amount": str(refund.amount),
            "total_refunded": str(total_refunded_for_payment),
            "payment_status": payment.payment_status,
            "invoice_status": invoice.status
        }
