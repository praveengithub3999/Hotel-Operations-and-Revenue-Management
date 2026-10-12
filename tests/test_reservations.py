from datetime import date, timedelta

from app.database.database import SessionLocal
from app.models.reservation import Reservation
from app.models.room import Room


def prepare_room(room_id, check_in, check_out):
    """Cancel existing test reservations that overlap the selected dates."""
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        assert room is not None

        db.query(Reservation).filter(
            Reservation.room_id == room_id,
            Reservation.status.in_(["PENDING", "CONFIRMED", "CHECKED_IN"]),
            Reservation.check_in_date < check_out,
            Reservation.check_out_date > check_in,
        ).update(
            {Reservation.status: "CANCELLED"},
            synchronize_session=False,
        )

        room.status = "AVAILABLE"
        db.commit()
    finally:
        db.close()


def test_create_reservation(admin_client):
    # Reset room 1 and clear any conflicting test reservations.
    check_in = date(2040, 1, 10)
    check_out = date(2040, 1, 12)
    prepare_room(1, check_in, check_out)

    response = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
            "number_of_guests": 2,
            "special_requests": "Late check-in",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["guest_id"] == 1
    assert data["room_id"] == 1
    assert data["status"] == "CONFIRMED"

def test_create_reservation_invalid_dates(admin_client):
    response = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": "2030-01-15",
            "check_out_date": "2030-01-10",
            "number_of_guests": 2,
            "special_requests": None,
        },
    )

    # The request schema rejects invalid date ranges.
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_create_overlapping_reservation(admin_client):
    check_in = date(2042, 2, 10)
    check_out = date(2042, 2, 12)
    prepare_room(1, check_in, date(2042, 2, 13))

    first = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
            "number_of_guests": 2,
            "special_requests": "Overlap test first reservation",
        },
    )
    assert first.status_code == 200, first.text

    response = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": "2042-02-11",
            "check_out_date": "2042-02-13",
            "number_of_guests": 2,
            "special_requests": "Overlap test second reservation",
        },
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == (
        "Room is already reserved for these dates"
    )


def test_room_availability(admin_client):
    check_in = date(2043, 3, 10)
    check_out = date(2043, 3, 12)
    prepare_room(1, check_in, date(2043, 3, 13))

    create_response = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
            "number_of_guests": 2,
            "special_requests": "Availability test reservation",
        },
    )
    assert create_response.status_code == 200, create_response.text

    response = admin_client.get(
        "/reservations/availability/1",
        params={
            "check_in_date": "2043-03-11",
            "check_out_date": "2043-03-13",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["room_id"] == 1
    assert data["available"] is False
    assert data["message"] == (
        "Room is already reserved for these dates"
    )


def test_successful_check_in(admin_client):
    today = date.today()
    check_out = today + timedelta(days=2)
    prepare_room(1, today, check_out)

    response = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": str(today),
            "check_out_date": str(check_out),
            "number_of_guests": 2,
            "special_requests": "Test check-in",
        },
    )
    assert response.status_code == 200, response.text
    reservation_id = response.json()["id"]

    response = admin_client.post(
        f"/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["reservation_id"] == reservation_id
    assert data["room_id"] == 1
    assert data["reservation_status"] == "CHECKED_IN"
    assert data["room_status"] == "OCCUPIED"


def test_check_in_before_reservation_date(admin_client):
    today = date.today()
    check_in = today + timedelta(days=5)
    check_out = check_in + timedelta(days=2)

    # Reset room status and clear conflicting reservations.
    prepare_room(2, check_in, check_out)

    response = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 2,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
            "number_of_guests": 2,
            "special_requests": "Future check-in",
        },
    )

    assert response.status_code == 200, response.text
    reservation_id = response.json()["id"]

    response = admin_client.post(
        f"/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == (
        "Check-in date has not arrived yet"
    )

def test_check_in_nonexistent_reservation(admin_client):
    response = admin_client.post("/reservations/99999/check-in")

    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"


def test_check_in_cancelled_reservation(admin_client):
    today = date.today()
    check_out = today + timedelta(days=2)
    prepare_room(2, today, check_out)

    response = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 2,
            "check_in_date": str(today),
            "check_out_date": str(check_out),
            "number_of_guests": 2,
            "special_requests": "Cancelled reservation test",
        },
    )
    assert response.status_code == 200, response.text
    reservation_id = response.json()["id"]

    response = admin_client.delete(
        f"/reservations/{reservation_id}"
    )
    assert response.status_code == 200, response.text

    response = admin_client.post(
        f"/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only confirmed reservations can be checked in"
    )


def test_check_in_maintenance_room(admin_client):
    today = date.today()
    check_out = today + timedelta(days=2)
    prepare_room(2, today, check_out)

    response = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 2,
            "check_in_date": str(today),
            "check_out_date": str(check_out),
            "number_of_guests": 2,
            "special_requests": "Maintenance room test",
        },
    )
    assert response.status_code == 200, response.text
    reservation_id = response.json()["id"]

    db = SessionLocal()
    try:
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id
        ).first()
        room = db.query(Room).filter(Room.id == 2).first()

        assert reservation is not None
        assert room is not None

        reservation.status = "CONFIRMED"
        room.status = "MAINTENANCE"
        db.commit()
    finally:
        db.close()

    response = admin_client.post(
        f"/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Room is not ready for check-in"
    )
