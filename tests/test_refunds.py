from datetime import date, timedelta

from app.database.database import SessionLocal
from app.models.reservation import Reservation
from app.models.invoice import Invoice
from app.models.payment import Payment


def create_test_payment():
    db = SessionLocal()

    try:
        reservation = Reservation(
            guest_id=1,
            room_id=1,
            check_in_date=date.today() + timedelta(days=20),
            check_out_date=date.today() + timedelta(days=22),
            number_of_guests=2,
            status="CONFIRMED",
            special_requests="Refund test"
        )

        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        invoice = Invoice(
            reservation_id=reservation.id,
            subtotal=5000,
            discount=0,
            tax=900,
            total=5900,
            status="PAID"
        )

        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        payment = Payment(
            invoice_id=invoice.id,
            amount=2000,
            payment_method="CARD",
            payment_status="SUCCESS",
            transaction_reference="REFUND-TEST-001"
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return payment.id

    finally:
        db.close()


def test_refund_nonexistent_payment(admin_client):
    response = admin_client.post(
        "/refunds/",
        json={
            "payment_id": 99999,
            "amount": "500.00"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_refund_zero_amount(admin_client):
    payment_id = create_test_payment()

    response = admin_client.post(
        "/refunds/",
        json={
            "payment_id": payment_id,
            "amount": "0"
        }
    )

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert response.json()["detail"][0]["loc"] == ["body", "amount"]


def test_refund_exceeds_payment_amount(admin_client):
    payment_id = create_test_payment()

    response = admin_client.post(
        "/refunds/",
        json={
            "payment_id": payment_id,
            "amount": "2500.00"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Refund amount exceeds the remaining refundable amount"
    )


def test_refund_successful(admin_client):
    payment_id = create_test_payment()

    response = admin_client.post(
        "/refunds/",
        json={
            "payment_id": payment_id,
            "amount": "500.00"
        }
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == "Refund processed successfully"
    assert data["payment_id"] == payment_id
    assert data["refund_amount"] == "500.00"
    assert data["payment_status"] == "PARTIALLY_REFUNDED"
