
from datetime import date

from app.models.reservation import Reservation
from app.models.service_request import ServiceRequest


def prepare_checked_in_reservation(admin_client):
    """Find a reservation that is checked in for service-request tests."""
    from app.database.database import SessionLocal

    db = SessionLocal()

    try:
        reservation = db.query(Reservation).filter(
            Reservation.status == "CHECKED_IN"
        ).first()

        if reservation:
            return reservation.id

        # Use the existing seeded reservation if available.
        reservation = db.query(Reservation).first()

        if not reservation:
            raise AssertionError(
                "No reservation found in the test database."
            )

        reservation.status = "CHECKED_IN"
        db.commit()
        return reservation.id
    finally:
        db.close()


def test_create_service_request_success(admin_client):
    reservation_id = prepare_checked_in_reservation(admin_client)

    response = admin_client.post(
        "/service-requests/",
        json={
            "reservation_id": reservation_id,
            "service_type": "ROOM_SERVICE",
            "description": "Extra towels",
            "quantity": 2,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["reservation_id"] == reservation_id
    assert data["service_type"] == "ROOM_SERVICE"
    assert data["quantity"] == 2
    assert data["status"] == "REQUESTED"


def test_create_service_request_missing_reservation(admin_client):
    response = admin_client.post(
        "/service-requests/",
        json={
            "reservation_id": 999999,
            "service_type": "ROOM_SERVICE",
            "description": "Extra towels",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"


def test_create_service_request_not_checked_in(admin_client):
    from app.database.database import SessionLocal

    db = SessionLocal()
    try:
        reservation = db.query(Reservation).first()
        assert reservation is not None

        reservation.status = "CONFIRMED"
        db.commit()
        reservation_id = reservation.id
    finally:
        db.close()

    response = admin_client.post(
        "/service-requests/",
        json={
            "reservation_id": reservation_id,
            "service_type": "ROOM_SERVICE",
            "description": "Extra towels",
            "quantity": 1,
        },
    )

    assert response.status_code == 400
    assert "active stay" in response.json()["detail"]


def test_list_service_requests(admin_client):
    response = admin_client.get("/service-requests/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_service_request_to_in_progress(admin_client):
    reservation_id = prepare_checked_in_reservation(admin_client)

    create_response = admin_client.post(
        "/service-requests/",
        json={
            "reservation_id": reservation_id,
            "service_type": "ROOM_SERVICE",
            "description": "Test request",
            "quantity": 1,
        },
    )
    assert create_response.status_code == 200, create_response.text
    service_id = create_response.json()["id"]

    response = admin_client.put(
        f"/service-requests/{service_id}",
        json={"status": "IN_PROGRESS"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "IN_PROGRESS"


def test_update_service_request_invalid_status(admin_client):
    reservation_id = prepare_checked_in_reservation(admin_client)

    create_response = admin_client.post(
        "/service-requests/",
        json={
            "reservation_id": reservation_id,
            "service_type": "ROOM_SERVICE",
            "description": "Test request",
            "quantity": 1,
        },
    )
    assert create_response.status_code == 200, create_response.text
    service_id = create_response.json()["id"]

    response = admin_client.put(
        f"/service-requests/{service_id}",
        json={"status": "UNKNOWN"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid service request status"


def test_update_missing_service_request(admin_client):
    response = admin_client.put(
        "/service-requests/999999",
        json={"status": "IN_PROGRESS"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Service request not found"


def test_complete_service_request(admin_client):
    reservation_id = prepare_checked_in_reservation(admin_client)

    create_response = admin_client.post(
        "/service-requests/",
        json={
            "reservation_id": reservation_id,
            "service_type": "ROOM_SERVICE",
            "description": "Test completion",
            "quantity": 1,
        },
    )
    assert create_response.status_code == 200, create_response.text
    service_id = create_response.json()["id"]

    start_response = admin_client.put(
        f"/service-requests/{service_id}",
        json={"status": "IN_PROGRESS"},
    )
    assert start_response.status_code == 200, start_response.text

    response = admin_client.put(
        f"/service-requests/{service_id}",
        json={"status": "COMPLETED"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["completed_at"] is not None


def test_cannot_reopen_completed_request(admin_client):
    reservation_id = prepare_checked_in_reservation(admin_client)

    create_response = admin_client.post(
        "/service-requests/",
        json={
            "reservation_id": reservation_id,
            "service_type": "ROOM_SERVICE",
            "description": "Completed request",
            "quantity": 1,
        },
    )
    assert create_response.status_code == 200, create_response.text
    service_id = create_response.json()["id"]

    admin_client.put(
        f"/service-requests/{service_id}",
        json={"status": "IN_PROGRESS"},
    )
    admin_client.put(
        f"/service-requests/{service_id}",
        json={"status": "COMPLETED"},
    )

    response = admin_client.put(
        f"/service-requests/{service_id}",
        json={"status": "IN_PROGRESS"},
    )

    assert response.status_code == 400
    assert "cannot be changed" in response.json()["detail"]


def test_invalid_status_transition(admin_client):
    reservation_id = prepare_checked_in_reservation(admin_client)

    create_response = admin_client.post(
        "/service-requests/",
        json={
            "reservation_id": reservation_id,
            "service_type": "ROOM_SERVICE",
            "description": "Transition test",
            "quantity": 1,
        },
    )
    assert create_response.status_code == 200, create_response.text
    service_id = create_response.json()["id"]

    response = admin_client.put(
        f"/service-requests/{service_id}",
        json={"status": "COMPLETED"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid status transition"
