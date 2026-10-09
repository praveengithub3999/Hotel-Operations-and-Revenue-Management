from fastapi.testclient import TestClient
from datetime import date, timedelta
from decimal import Decimal

from app.main import app
from app.database.database import SessionLocal
from app.models.reservation import Reservation
from app.models.invoice import Invoice

client = TestClient(app)


def create_test_invoice():
    db = SessionLocal()

    reservation = Reservation(
        guest_id=1,
        room_id=1,
        check_in_date=date.today() + timedelta(days=10),
        check_out_date=date.today() + timedelta(days=12),
        number_of_guests=2,
        status="CONFIRMED",
        special_requests="Payment test"
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
        status="UNPAID"
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    invoice_id = invoice.id

    db.close()

    return invoice_id


def test_payment_with_nonexistent_invoice():
    response = client.post(
        "/payments/",
        json={
            "invoice_id": 99999,
            "amount": "1000.00",
            "payment_method": "CASH"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_payment_with_zero_amount():
    invoice_id = create_test_invoice()

    response = client.post(
        "/payments/",
        json={
            "invoice_id": invoice_id,
            "amount": "0",
            "payment_method": "CASH"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Payment amount must be greater than zero"


def test_payment_with_invalid_method():
    invoice_id = create_test_invoice()

    response = client.post(
        "/payments/",
        json={
            "invoice_id": invoice_id,
            "amount": "1000.00",
            "payment_method": "BITCOIN"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid payment method"

def test_successful_payment():
    invoice_id = create_test_invoice()

    response = client.post(
        "/payments/",
        json={
            "invoice_id": invoice_id,
            "amount": "1000.00",
            "payment_method": "CARD",
            "transaction_reference": "TEST-TXN-001"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["invoice_id"] == invoice_id
    assert data["amount"] == "1000.00"
    assert data["payment_method"] == "CARD"
    assert data["payment_status"] == "SUCCESS"
    assert data["transaction_reference"] == "TEST-TXN-001"


def test_payment_exceeds_invoice_total():
    invoice_id = create_test_invoice()

    response = client.post(
        "/payments/",
        json={
            "invoice_id": invoice_id,
            "amount": "6000.00",
            "payment_method": "UPI"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Payment amount exceeds invoice total"


def test_full_payment_marks_invoice_paid():
    invoice_id = create_test_invoice()

    response = client.post(
        "/payments/",
        json={
            "invoice_id": invoice_id,
            "amount": "5900.00",
            "payment_method": "CASH",
            "transaction_reference": "FULL-PAY-001"
        }
    )

    assert response.status_code == 200

    # Check invoice status directly in database
    db = SessionLocal()

    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id
    ).first()

    assert invoice.status == "PAID"

    db.close()