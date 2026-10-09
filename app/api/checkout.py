from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.reservation import Reservation
from app.models.room import Room
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.housekeeping import Housekeeping
from app.utils.audit_logger import create_audit_log


router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"]
)


@router.post("/{reservation_id}")
def checkout(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    # Find reservation
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    # Reservation must be checked in
    if reservation.status != "CHECKED_IN":
        raise HTTPException(
            status_code=400,
            detail="Guest must be checked in before checkout"
        )

    # Find invoice
    invoice = db.query(Invoice).filter(
        Invoice.reservation_id == reservation_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=400,
            detail="Invoice not found"
        )

    # Calculate successful payments
    payments = db.query(Payment).filter(
        Payment.invoice_id == invoice.id,
        Payment.payment_status == "SUCCESS"
    ).all()

    paid_amount = sum(
        (payment.amount for payment in payments),
        start=0
    )

    # Payment must cover invoice
    if paid_amount < invoice.total:
        raise HTTPException(
            status_code=400,
            detail="Payment is not completed"
        )

    # Find room
    room = db.query(Room).filter(
        Room.id == reservation.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    # Complete reservation
    reservation.status = "CHECKED_OUT"

    # Room becomes dirty after checkout
    room.status = "DIRTY"
    housekeeping_task = Housekeeping(
        room_id=room.id,
        status="DIRTY",
        notes="Room needs cleaning after checkout"
    )
    db.add(housekeeping_task)

    db.commit()
    db.refresh(reservation)

    create_audit_log(
        action="CHECKOUT",
        message="Guest checked out successfully",
        reservation_id = reservation.id
    )

    return {
        "message": "Checkout completed successfully",
        "reservation_id": reservation.id,
        "invoice_id": invoice.id,
        "room_id": room.id,
        "room_status": room.status,
        "reservation_status": reservation.status
    }