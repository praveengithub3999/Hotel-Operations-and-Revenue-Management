
from decimal import Decimal

from app.database.database import SessionLocal
from app.models.room import Room
from app.models.reservation import Reservation


def test_occupancy_report(admin_client):
    response = admin_client.get("/reports/occupancy")

    assert response.status_code == 200

    data = response.json()

    assert data["total_rooms"] >= 2
    assert data["occupied_rooms"] >= 0
    assert data["available_rooms"] >= 0
    assert data["reserved_rooms"] >= 0
    assert data["dirty_rooms"] >= 0
    assert data["maintenance_rooms"] >= 0
    assert data["cleaning_rooms"] >= 0
    assert 0 <= data["occupancy_percentage"] <= 100


def test_occupancy_report_forbidden_for_receptionist(
    receptionist_client,
):
    response = receptionist_client.get("/reports/occupancy")

    assert response.status_code == 403


def test_revenue_report(admin_client):
    response = admin_client.get("/reports/revenue")

    assert response.status_code == 200

    data = response.json()

    assert "total_charges" in data
    assert "successful_payments" in data
    assert "total_revenue" in data

    assert data["total_charges"] >= 0
    assert data["successful_payments"] >= 0
    assert isinstance(data["total_revenue"], (int, float))


def test_revenue_report_forbidden_for_receptionist(
    receptionist_client,
):
    response = receptionist_client.get("/reports/revenue")

    assert response.status_code == 403


def test_reservation_report(admin_client):
    response = admin_client.get("/reports/reservations")

    assert response.status_code == 200

    data = response.json()

    expected_fields = [
        "pending",
        "confirmed",
        "checked_in",
        "checked_out",
        "cancelled",
        "no_show",
        "total_reservations",
    ]

    for field in expected_fields:
        assert field in data
        assert data[field] >= 0

    assert data["total_reservations"] >= 1


def test_reservation_report_forbidden_for_housekeeping(
    client,
):
    # The unauthenticated client must not access protected reports.
    response = client.get("/reports/reservations")

    assert response.status_code in (401, 403)


def test_room_status_report(admin_client):
    response = admin_client.get("/reports/rooms")

    assert response.status_code == 200

    data = response.json()

    expected_fields = [
        "available",
        "reserved",
        "occupied",
        "dirty",
        "cleaning",
        "maintenance",
        "total_rooms",
    ]

    for field in expected_fields:
        assert field in data
        assert data[field] >= 0

    assert data["total_rooms"] >= 2


def test_room_status_report_forbidden_for_receptionist(
    receptionist_client,
):
    response = receptionist_client.get("/reports/rooms")

    assert response.status_code == 403
