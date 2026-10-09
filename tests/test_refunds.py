from fastapi.testclient import TestClient
from datetime import date, timedelta

from app.main import app
from app.database.database import SessionLocal
from app.models.reservation import Reservation
from app.models.invoice import Invoice
from app.models.payment import Payment

client = TestClient(app)


def create_test_payment():
    db = SessionLocal()

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

    payment_id = payment.id

    db.close()

    return payment_id


def test_refund_nonexistent_payment():
    response = client.post(
        "/refunds/",
        json={
            "payment_id": 99999,
            "amount": "500.00"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_refund_zero_amount():
    payment_id = create_test_payment()

    response = client.post(
        "/refunds/",
        json={
            "payment_id": payment_id,
            "amount": "0"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Refund amount must be greater than zero"


def test_refund_exceeds_payment_amount():
    payment_id = create_test_payment()

    response = client.post(
        "/refunds/",
        json={
            "payment_id": payment_id,
            "amount": "2500.00"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Refund amount cannot exceed payment amount"


def test_refund_successful():
    payment_id = create_test_payment()

    response = client.post(
        "/refunds/",
        json={
            "payment_id": payment_id,
            "amount": "500.00"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Refund processed successfully"
    assert data["payment_id"] == payment_id
    assert data["refund_amount"] == 500.00
    assert data["payment_status"] == "PARTIALLY_REFUNDED"