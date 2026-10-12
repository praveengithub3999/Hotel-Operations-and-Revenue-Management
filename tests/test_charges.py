
from decimal import Decimal

from app.database.database import SessionLocal
from app.models.charge import Charge
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.reservation import Reservation


def create_test_charge_reservation(status="CONFIRMED"):
    """Create a separate reservation for charge tests."""
    db = SessionLocal()

    try:
        reservation = db.query(Reservation).filter(
            Reservation.special_requests == "Payment test reservation"
        ).first()

        assert reservation is not None, "Test reservation was not seeded"

        reservation.status = status
        db.flush()

        # Remove prior test charges and payment records for this invoice.
        invoice = db.query(Invoice).filter(
            Invoice.reservation_id == reservation.id
        ).first()

        if invoice:
            db.query(Payment).filter(
                Payment.invoice_id == invoice.id
            ).delete(synchronize_session=False)

            db.query(Charge).filter(
                Charge.reservation_id == reservation.id
            ).delete(synchronize_session=False)

            invoice.status = "UNPAID"

        db.commit()
        return reservation.id, invoice.id if invoice else None

    finally:
        db.close()


def test_create_charge_success(admin_client):
    reservation_id, _ = create_test_charge_reservation()

    response = admin_client.post(
        "/charges/",
        json={
            "reservation_id": reservation_id,
            "charge_type": "MINIBAR",
            "description": "Drinks and snacks",
            "quantity": 2,
            "unit_price": "150.00",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["reservation_id"] == reservation_id
    assert data["charge_type"] == "MINIBAR"
    assert data["quantity"] == 2
    assert Decimal(str(data["total_amount"])) == Decimal("300.00")


def test_create_charge_reservation_not_found(admin_client):
    response = admin_client.post(
        "/charges/",
        json={
            "reservation_id": 999999,
            "charge_type": "MINIBAR",
            "description": "Test charge",
            "quantity": 1,
            "unit_price": "100.00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"


def test_create_charge_invalid_reservation_status(admin_client):
    reservation_id, _ = create_test_charge_reservation(
        status="CANCELLED"
    )

    response = admin_client.post(
        "/charges/",
        json={
            "reservation_id": reservation_id,
            "charge_type": "MINIBAR",
            "description": "Test charge",
            "quantity": 1,
            "unit_price": "100.00",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Charges cannot be added to this reservation"
    )


def test_create_charge_invoice_not_unpaid(admin_client):
    reservation_id, invoice_id = create_test_charge_reservation()

    assert invoice_id is not None, "Test invoice was not seeded"

    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).first()
        invoice.status = "PAID"
        db.commit()
    finally:
        db.close()

    response = admin_client.post(
        "/charges/",
        json={
            "reservation_id": reservation_id,
            "charge_type": "MINIBAR",
            "description": "Test charge",
            "quantity": 1,
            "unit_price": "100.00",
        },
    )

    assert response.status_code == 400
    assert "after payment or refund" in response.json()["detail"]


def test_create_charge_existing_payment(admin_client):
    reservation_id, invoice_id = create_test_charge_reservation()

    assert invoice_id is not None, "Test invoice was not seeded"

    db = SessionLocal()
    try:
        # Add a payment record to trigger the payment restriction.
        payment = Payment(
            invoice_id=invoice_id,
            amount=Decimal("10.00"),
            payment_method="CASH",
        )
        db.add(payment)
        db.commit()
    finally:
        db.close()

    response = admin_client.post(
        "/charges/",
        json={
            "reservation_id": reservation_id,
            "charge_type": "MINIBAR",
            "description": "Test charge",
            "quantity": 1,
            "unit_price": "100.00",
        },
    )

    assert response.status_code == 400
    assert "payment records exist" in response.json()["detail"]


def test_get_reservation_charges(admin_client):
    reservation_id, _ = create_test_charge_reservation()

    create_response = admin_client.post(
        "/charges/",
        json={
            "reservation_id": reservation_id,
            "charge_type": "LAUNDRY",
            "description": "Laundry service",
            "quantity": 3,
            "unit_price": "50.00",
        },
    )
    assert create_response.status_code == 200, create_response.text

    response = admin_client.get(f"/charges/{reservation_id}")

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)
    assert any(
        charge["charge_type"] == "LAUNDRY"
        for charge in response.json()
    )


def test_get_charges_reservation_not_found(admin_client):
    response = admin_client.get("/charges/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"
