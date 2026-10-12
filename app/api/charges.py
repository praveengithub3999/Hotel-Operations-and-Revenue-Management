from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.charge import Charge
from app.models.reservation import Reservation
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.charge import ChargeCreate, ChargeResponse

router = APIRouter(
    prefix="/charges",
    tags=["Charges"]
)


@router.post(
    "/",
    response_model=ChargeResponse,
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST"))]
)
def create_charge(
    charge: ChargeCreate,
    db: Session = Depends(get_db)
):
    try:
        reservation = db.query(Reservation).filter(
            Reservation.id == charge.reservation_id
        ).with_for_update().first()

        if not reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )

        if reservation.status not in ["CONFIRMED", "CHECKED_IN"]:
            raise HTTPException(
                status_code=400,
                detail="Charges cannot be added to this reservation"
            )

        invoice = db.query(Invoice).filter(
            Invoice.reservation_id == reservation.id
        ).with_for_update().first()

        if invoice:
            if invoice.status != "UNPAID":
                raise HTTPException(
                    status_code=400,
                    detail="Cannot add charges after payment or refund processing"
                )

            existing_payments = db.query(Payment).filter(
                Payment.invoice_id == invoice.id
            ).first()

            if existing_payments:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot add charges when payment records exist"
                )

        total_amount = (
            charge.unit_price * charge.quantity
        ).quantize(Decimal("0.01"))

        new_charge = Charge(
            reservation_id=reservation.id,
            charge_type=charge.charge_type.strip(),
            description=charge.description,
            quantity=charge.quantity,
            unit_price=charge.unit_price,
            total_amount=total_amount
        )

        db.add(new_charge)
        db.commit()
        db.refresh(new_charge)

        return new_charge

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get(
    "/{reservation_id}",
    response_model=list[ChargeResponse],
    dependencies=[
        Depends(
            require_role(
                "ADMIN",
                "RECEPTIONIST",
                "FINANCE",
                "MANAGER"
            )
        )
    ]
)
def get_reservation_charges(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    return db.query(Charge).filter(
        Charge.reservation_id == reservation_id
    ).all()
