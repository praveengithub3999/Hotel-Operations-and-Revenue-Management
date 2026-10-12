from datetime import date, timedelta
from decimal import Decimal

from app.database.database import SessionLocal
from app.models.reservation import Reservation
from app.models.room import Room
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.housekeeping import Housekeeping


def create_checkout_data(
    reservation_status="CHECKED_IN",
    invoice_status="UNPAID",
    invoice_total=Decimal("1000.00"),
    payment_amount=None,
    room_id=1,
):
    """Create separate reservation, invoice, and optional payment data."""
    db = SessionLocal()

    try:
        reservation = Reservation(
            guest_id=1,
            room_id=room_id,
            check_in_date=date.today() - timedelta(days=1),
            check_out_date=date.today() + timedelta(days=1),
            number_of_guests=1,
            status=reservation_status,
            special_requests="Checkout test",
        )
        db.add(reservation)
        db.flush()

        invoice = Invoice(
            reservation_id=reservation.id,
            subtotal=invoice_total,
            discount=0,
            tax_percentage=0,
            tax=0,
            total=invoice_total,
            status=invoice_status,
        )
        db.add(invoice)
        db.flush()

        if payment_amount is not None:
            payment = Payment(
                invoice_id=invoice.id,
                amount=payment_amount,
                payment_method="CARD",
                payment_status="SUCCESS",
                transaction_reference=f"CHECKOUT-{reservation.id}",
            )
            db.add(payment)

        room = db.query(Room).filter(Room.id == room_id).first()
        assert room is not None
        room.status = "OCCUPIED"

        db.commit()
        return reservation.id, invoice.id

    finally:
        db.close()


def test_checkout_reservation_not_found(admin_client):
    response = admin_client.post("/checkout/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"


def test_checkout_guest_not_checked_in(admin_client):
    reservation_id, _ = create_checkout_data(
        reservation_status="CONFIRMED"
    )

    response = admin_client.post(f"/checkout/{reservation_id}")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Guest must be checked in before checkout"
    )


def test_checkout_invoice_not_found(admin_client):
    reservation_id, invoice_id = create_checkout_data()

    db = SessionLocal()
    try:
        db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

    response = admin_client.post(f"/checkout/{reservation_id}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invoice not found"


def test_checkout_refunded_invoice(admin_client):
    reservation_id, invoice_id = create_checkout_data(
        invoice_status="REFUNDED",
        payment_amount=Decimal("1000.00"),
    )

    response = admin_client.post(f"/checkout/{reservation_id}")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Cannot checkout with a refunded invoice"
    )


def test_checkout_outstanding_balance(admin_client):
    reservation_id, _ = create_checkout_data(
        invoice_total=Decimal("1000.00"),
        payment_amount=Decimal("500.00"),
    )

    response = admin_client.post(f"/checkout/{reservation_id}")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Outstanding invoice balance must be paid before checkout"
    )


def test_checkout_success_creates_housekeeping_task(admin_client):
    reservation_id, invoice_id = create_checkout_data(
        invoice_total=Decimal("1000.00"),
        payment_amount=Decimal("1000.00"),
    )

    response = admin_client.post(f"/checkout/{reservation_id}")

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["message"] == "Checkout completed successfully"
    assert data["reservation_id"] == reservation_id
    assert data["invoice_id"] == invoice_id
    assert data["room_id"] == 1
    assert data["reservation_status"] == "CHECKED_OUT"
    assert data["room_status"] == "DIRTY"
    assert Decimal(data["net_paid_amount"]) == Decimal("1000.00")

    db = SessionLocal()
    try:
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id
        ).first()
        room = db.query(Room).filter(Room.id == 1).first()
        task = db.query(Housekeeping).filter(
            Housekeeping.room_id == 1,
            Housekeeping.notes == "Room needs cleaning after checkout",
        ).order_by(Housekeeping.id.desc()).first()

        assert reservation.status == "CHECKED_OUT"
        assert room.status == "DIRTY"
        assert task is not None
        assert task.status == "DIRTY"
    finally:
        db.close()


def test_checkout_deducts_successful_refund(admin_client):
    reservation_id, invoice_id = create_checkout_data(
        invoice_total=Decimal("1000.00"),
        payment_amount=Decimal("1200.00"),
    )

    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(
            Payment.invoice_id == invoice_id
        ).first()
        assert payment is not None

        refund = Refund(
            payment_id=payment.id,
            amount=Decimal("300.00"),
            status="SUCCESS",
        )
        db.add(refund)
        db.commit()
    finally:
        db.close()

    response = admin_client.post(f"/checkout/{reservation_id}")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Outstanding invoice balance must be paid before checkout"
    )
