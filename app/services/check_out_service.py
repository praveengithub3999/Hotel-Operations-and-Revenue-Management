from decimal import Decimal
from typing import Any, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.models.room import Room
from app.models.room_type import RoomType
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.charge import Charge
from app.models.housekeeping import Housekeeping
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.hotel_repository import RoomRepository
from app.repositories.billing_repository import InvoiceRepository, PaymentRepository, RefundRepository, ChargeRepository
from app.utils.audit_logger import create_audit_log, create_housekeeping_log


class CheckOutService:
    def __init__(self, db: Session):
        self.db = db
        self.reservation_repo = ReservationRepository(db)
        self.room_repo = RoomRepository(db)
        self.invoice_repo = InvoiceRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.refund_repo = RefundRepository(db)
        self.charge_repo = ChargeRepository(db)

    def check_out_guest(self, reservation_id: int) -> Dict[str, Any]:
        # Lock reservation to prevent concurrent checkouts
        reservation = self.reservation_repo.get_by_id(reservation_id, for_update=True)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if reservation.status != "CHECKED_IN":
            raise HTTPException(
                status_code=400,
                detail="Guest must be checked in before checkout"
            )

        invoice = self.invoice_repo.find_by_reservation(reservation_id, for_update=True)
        if not invoice:
            raise HTTPException(
                status_code=400,
                detail="Invoice not found"
            )

        if invoice.status == "REFUNDED":
            raise HTTPException(
                status_code=400,
                detail="Cannot checkout with a refunded invoice"
            )

        # Lock payment records before calculating balance
        payments = self.payment_repo.get_by_invoice(invoice.id, for_update=True)
        paid_amount = Decimal("0.00")

        for payment in payments:
            if payment.payment_status not in [
                "SUCCESS",
                "PARTIALLY_REFUNDED",
                "REFUNDED"
            ]:
                continue

            refunds = self.refund_repo.get_by_payment(payment.id)
            refunded_amount = sum(
                (refund.amount for refund in refunds if refund.status == "SUCCESS"),
                Decimal("0.00")
            )
            paid_amount += payment.amount - refunded_amount

        if paid_amount < invoice.total:
            raise HTTPException(
                status_code=400,
                detail="Outstanding invoice balance must be paid before checkout"
            )

        room = self.room_repo.get_by_id(reservation.room_id, for_update=True)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        reservation.status = "CHECKED_OUT"
        room.status = "DIRTY"

        housekeeping_task = Housekeeping(
            room_id=room.id,
            status="DIRTY",
            task_type="CLEANING",
            priority="HIGH",
            notes="Room needs cleaning after checkout",
            remarks="Automated post-checkout housekeeping trigger"
        )
        self.db.add(housekeeping_task)

        # Audit log in MongoDB
        create_audit_log(
            action="CHECKOUT",
            message=f"Guest checked out from room {room.room_number}",
            reservation_id=reservation.id,
            entity="reservation",
            entity_id=reservation.id,
            details={"room_id": room.id, "room": room.room_number, "net_paid": str(paid_amount)}
        )

        create_housekeeping_log(
            room=room.room_number,
            staff=None,
            action="CHECKOUT_DIRTY",
            old_status="OCCUPIED",
            new_status="DIRTY",
            remarks="Room marked DIRTY on guest checkout"
        )

        self.db.commit()
        self.db.refresh(reservation)

        return {
            "message": "Checkout completed successfully",
            "reservation_id": reservation.id,
            "invoice_id": invoice.id,
            "room_id": room.id,
            "room_status": room.status,
            "reservation_status": reservation.status,
            "net_paid_amount": str(paid_amount)
        }
