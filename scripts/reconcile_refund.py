
from decimal import Decimal

from app.database.database import SessionLocal
from app.models.payment import Payment
from app.models.refund import Refund

db = SessionLocal()

try:
    payment = (
        db.query(Payment)
        .filter(Payment.id == 2)
        .with_for_update()
        .first()
    )

    if not payment:
        raise ValueError("Payment #2 was not found")

    existing = (
        db.query(Refund)
        .filter(
            Refund.payment_id == 2,
            Refund.status == "SUCCESS"
        )
        .all()
    )

    already_recorded = sum(
        (refund.amount for refund in existing),
        Decimal("0.00")
    )

    if already_recorded >= Decimal("1000.00"):
        print("The historical refund is already recorded.")
    else:
        if already_recorded != Decimal("0.00"):
            raise ValueError(
                "Unexpected existing refund amount. "
                "Stop and review before proceeding."
            )

        if payment.payment_status != "PARTIALLY_REFUNDED":
            raise ValueError(
                "Payment status is not PARTIALLY_REFUNDED"
            )

        refund = Refund(
            payment_id=2,
            amount=Decimal("1000.00"),
            status="SUCCESS"
        )

        db.add(refund)
        db.commit()

        print("Historical refund recorded successfully.")
        print("Payment ID:", payment.id)
        print("Recorded refund: 1000.00")
        print("Remaining refundable amount: 2300.00")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
