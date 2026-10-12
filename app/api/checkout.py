from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.reservation import Reservation
from app.models.room import Room
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.housekeeping import Housekeeping
from app.utils.audit_logger import create_audit_log


router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"]
)


@router.post(
    "/{reservation_id}",
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def checkout(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Lock the reservation to prevent concurrent checkouts.
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id
        ).with_for_update().first()

        if not reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )

        if reservation.status != "CHECKED_IN":
            raise HTTPException(
                status_code=400,
                detail="Guest must be checked in before checkout"
            )

        invoice = db.query(Invoice).filter(
            Invoice.reservation_id == reservation_id
        ).with_for_update().first()

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

        # Lock payment records before calculating the balance.
        payments = db.query(Payment).filter(
            Payment.invoice_id == invoice.id
        ).with_for_update().all()

        paid_amount = Decimal("0.00")

        for payment in payments:
            if payment.payment_status not in [
                "SUCCESS",
                "PARTIALLY_REFUNDED",
                "REFUNDED"
            ]:
                continue

            refunds = db.query(Refund).filter(
                Refund.payment_id == payment.id,
                Refund.status == "SUCCESS"
            ).all()

            refunded_amount = sum(
                (refund.amount for refund in refunds),
                Decimal("0.00")
            )

            paid_amount += payment.amount - refunded_amount

        if paid_amount < invoice.total:
            raise HTTPException(
                status_code=400,
                detail="Outstanding invoice balance must be paid before checkout"
            )

        room = db.query(Room).filter(
            Room.id == reservation.room_id
        ).with_for_update().first()

        if not room:
            raise HTTPException(
                status_code=404,
                detail="Room not found"
            )

        reservation.status = "CHECKED_OUT"
        room.status = "DIRTY"

        housekeeping_task = Housekeeping(
            room_id=room.id,
            status="DIRTY",
            notes="Room needs cleaning after checkout"
        )

        db.add(housekeeping_task)

        # Keep the audit log in the same transaction if the logger
        # uses this database session and does not commit independently.
        create_audit_log(
            action="CHECKOUT",
            message="Guest checked out successfully",
            reservation_id=reservation.id
        )

        db.commit()
        db.refresh(reservation)

        return {
            "message": "Checkout completed successfully",
            "reservation_id": reservation.id,
            "invoice_id": invoice.id,
            "room_id": room.id,
            "room_status": room.status,
            "reservation_status": reservation.status,
            "net_paid_amount": str(paid_amount)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
