from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.charge import Charge
from app.models.reservation import Reservation
from app.schemas.charge import ChargeCreate, ChargeResponse


router = APIRouter(
    prefix="/charges",
    tags=["Charges"]
)


@router.post(
    "/",
    response_model=ChargeResponse
)
def create_charge(
    charge: ChargeCreate,
    db: Session = Depends(get_db)
):
    reservation = db.query(Reservation).filter(
        Reservation.id == charge.reservation_id
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    if reservation.status not in [
        "CONFIRMED",
        "CHECKED_IN"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Charges cannot be added to this reservation"
        )

    if charge.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    if charge.unit_price < 0:
        raise HTTPException(
            status_code=400,
            detail="Unit price cannot be negative"
        )

    total_amount = (
        charge.unit_price * charge.quantity
    )

    new_charge = Charge(
        reservation_id=charge.reservation_id,
        charge_type=charge.charge_type,
        description=charge.description,
        quantity=charge.quantity,
        unit_price=charge.unit_price,
        total_amount=total_amount
    )

    db.add(new_charge)
    db.commit()
    db.refresh(new_charge)

    return new_charge


@router.get(
    "/{reservation_id}",
    response_model=list[ChargeResponse]
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

    charges = db.query(Charge).filter(
        Charge.reservation_id == reservation_id
    ).all()

    return charges