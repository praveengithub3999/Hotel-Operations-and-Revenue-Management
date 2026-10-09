from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_reservation():
    response = client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": "2040-01-10",
            "check_out_date": "2040-01-12",
            "number_of_guests": 2,
            "special_requests": "Late check-in"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["guest_id"] == 1
    assert data["room_id"] == 1
    assert data["status"] == "CONFIRMED"

def test_create_reservation_invalid_dates():
    response = client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": "2030-01-15",
            "check_out_date": "2030-01-10",
            "number_of_guests": 2,
            "special_requests": None
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Check-out date must be after check-in date"
    )

def test_create_overlapping_reservation():
    response = client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": "2040-01-11",
            "check_out_date": "2040-01-13",
            "number_of_guests": 2,
            "special_requests": None
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Room is already reserved for these dates"
    )
def test_room_availability():
    response = client.get(
        "/reservations/availability/1",
        params={
            "check_in_date": "2040-01-11",
            "check_out_date": "2040-01-13"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["room_id"] == 1
    assert data["available"] is False
    assert data["message"] == (
        "Room is already reserved for these dates"
    )
def test_successful_check_in():
    response = client.post(
        "/reservations/1/check-in"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["reservation_id"] == 1
    assert data["room_id"] == 1
    assert data["reservation_status"] == "CHECKED_IN"
    assert data["room_status"] == "OCCUPIED"

def test_successful_check_in():
    today = date.today()

    response = client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": str(today),
            "check_out_date": str(today + timedelta(days=2)),
            "number_of_guests": 2,
            "special_requests": "Test check-in"
        }
    )

    assert response.status_code == 200

    reservation_id = response.json()["id"]

    response = client.post(
        f"/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["reservation_id"] == reservation_id
    assert data["room_id"] == 1
    assert data["reservation_status"] == "CHECKED_IN"
    assert data["room_status"] == "OCCUPIED"

def test_check_in_before_reservation_date():
    today = date.today()

    response = client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 2,
            "check_in_date": str(today + timedelta(days=5)),
            "check_out_date": str(today + timedelta(days=7)),
            "number_of_guests": 2,
            "special_requests": "Future check-in"
        }
    )

    assert response.status_code == 200

    reservation_id = response.json()["id"]

    response = client.post(
        f"/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Check-in date has not arrived yet"

def test_check_in_nonexistent_reservation():
    response = client.post(
        "/reservations/99999/check-in"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"


def test_check_in_cancelled_reservation():
    today = date.today()

    # Create reservation
    response = client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 2,
            "check_in_date": str(today),
            "check_out_date": str(today + timedelta(days=2)),
            "number_of_guests": 2,
            "special_requests": "Cancelled reservation test"
        }
    )

    assert response.status_code == 200

    reservation_id = response.json()["id"]

    # Cancel reservation
    response = client.delete(
        f"/reservations/{reservation_id}"
    )

    assert response.status_code == 200

    # Try check-in
    response = client.post(
        f"/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only confirmed reservations can be checked in"


def test_check_in_maintenance_room():
    today = date.today()

    # Create reservation
    response = client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 2,
            "check_in_date": str(today),
            "check_out_date": str(today + timedelta(days=2)),
            "number_of_guests": 2,
            "special_requests": "Maintenance room test"
        }
    )

    assert response.status_code == 200

    reservation_id = response.json()["id"]

    # Manually change reservation to CONFIRMED
    from app.database.database import SessionLocal
    from app.models.reservation import Reservation
    from app.models.room import Room

    db = SessionLocal()

    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id
    ).first()

    room = db.query(Room).filter(
        Room.id == 2
    ).first()

    reservation.status = "CONFIRMED"
    room.status = "MAINTENANCE"

    db.commit()
    db.close()

    # Try check-in
    response = client.post(
        f"/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Room is not available for check-in"
