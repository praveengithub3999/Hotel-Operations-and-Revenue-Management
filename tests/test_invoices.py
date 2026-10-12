from decimal import Decimal

from app.database.database import SessionLocal
from app.models.reservation import Reservation
from app.models.invoice import Invoice
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.refund import Refund

def create_reservation_for_invoice():
    """Create a reservation with charges for invoice tests."""
    db = SessionLocal()

    try:
        reservation = db.query(Reservation).filter(
            Reservation.special_requests == "Invoice coverage test"
        ).first()

        if reservation:
            db.query(Refund).filter(
                Refund.payment_id.in_(
                    db.query(Payment.id).filter(
                        Payment.invoice_id.in_(
                            db.query(Invoice.id).filter(
                                Invoice.reservation_id == reservation.id
                            )
                        )
                    )
                )
            ).delete(synchronize_session=False)

            db.query(Payment).filter(
                Payment.invoice_id.in_(
                    db.query(Invoice.id).filter(
                        Invoice.reservation_id == reservation.id
                    )
                )
            ).delete(synchronize_session=False)

            db.query(Charge).filter(
                Charge.reservation_id == reservation.id
            ).delete(synchronize_session=False)

            db.query(Invoice).filter(
                Invoice.reservation_id == reservation.id
            ).delete(synchronize_session=False)

            db.query(Reservation).filter(
                Reservation.id == reservation.id
            ).delete(synchronize_session=False)

        reservation = Reservation(
            guest_id=1,
            room_id=1,
            check_in_date="2048-01-10",
            check_out_date="2048-01-12",
            number_of_guests=2,
            status="CONFIRMED",
            special_requests="Invoice coverage test",
        )
        db.add(reservation)
        db.flush()

        db.add_all([
            Charge(
                reservation_id=reservation.id,
                charge_type="ROOM",
                description="Room charge",
                quantity=1,
                unit_price=Decimal("1000.00"),
                total_amount=Decimal("1000.00"),
            ),
            Charge(
                reservation_id=reservation.id,
                charge_type="SERVICE",
                description="Service charge",
                quantity=1,
                unit_price=Decimal("200.00"),
                total_amount=Decimal("200.00"),
            ),
        ])

        db.commit()
        return reservation.id

    finally:
        db.close()


def test_create_invoice_success(admin_client):
    reservation_id = create_reservation_for_invoice()

    response = admin_client.post(
        "/invoices/",
        json={
            "reservation_id": reservation_id,
            "discount": "100",
            "tax_percentage": "10",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["reservation_id"] == reservation_id
    assert Decimal(data["subtotal"]) == Decimal("1200.00")
    assert Decimal(data["discount"]) == Decimal("100")
    assert Decimal(data["tax_percentage"]) == Decimal("10")
    assert Decimal(data["tax"]) == Decimal("110.00")
    assert Decimal(data["total"]) == Decimal("1210.00")
    assert data["status"] == "UNPAID"


def test_create_invoice_reservation_not_found(admin_client):
    response = admin_client.post(
        "/invoices/",
        json={
            "reservation_id": 999999,
            "discount": "0",
            "tax_percentage": "10",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"


def test_create_duplicate_invoice(admin_client):
    reservation_id = create_reservation_for_invoice()

    first = admin_client.post(
        "/invoices/",
        json={"reservation_id": reservation_id},
    )
    assert first.status_code == 200, first.text

    second = admin_client.post(
        "/invoices/",
        json={"reservation_id": reservation_id},
    )

    assert second.status_code == 400
    assert second.json()["detail"] == (
        "Invoice already exists for this reservation"
    )


def test_create_invoice_discount_greater_than_subtotal(admin_client):
    reservation_id = create_reservation_for_invoice()

    response = admin_client.post(
        "/invoices/",
        json={
            "reservation_id": reservation_id,
            "discount": "1500",
            "tax_percentage": "10",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Discount cannot be greater than subtotal"
    )


def test_create_invoice_tax_percentage_over_100(admin_client):
    reservation_id = create_reservation_for_invoice()

    response = admin_client.post(
        "/invoices/",
        json={
            "reservation_id": reservation_id,
            "discount": "0",
            "tax_percentage": "101",
        },
    )

    assert response.status_code == 422


def test_list_invoices(admin_client):
    response = admin_client.get("/invoices/")

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_get_invoice_not_found(admin_client):
    response = admin_client.get("/invoices/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_recalculate_invoice_success(admin_client):
    reservation_id = create_reservation_for_invoice()

    create_response = admin_client.post(
        "/invoices/",
        json={
            "reservation_id": reservation_id,
            "discount": "100",
            "tax_percentage": "10",
        },
    )
    assert create_response.status_code == 200, create_response.text
    invoice_id = create_response.json()["id"]

    db = SessionLocal()
    try:
        charge = Charge(
            reservation_id=reservation_id,
            charge_type="SERVICE",
            description="Additional service",
            quantity=1,
            unit_price=Decimal("300.00"),
            total_amount=Decimal("300.00"),
        )
        db.add(charge)
        db.commit()
    finally:
        db.close()

    response = admin_client.post(
        f"/invoices/{invoice_id}/recalculate"
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert Decimal(data["subtotal"]) == Decimal("1500.00")
    assert Decimal(data["discount"]) == Decimal("100")
    assert Decimal(data["tax"]) == Decimal("140.00")
    assert Decimal(data["total"]) == Decimal("1540.00")


def test_recalculate_invoice_not_found(admin_client):
    response = admin_client.post(
        "/invoices/999999/recalculate"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"
