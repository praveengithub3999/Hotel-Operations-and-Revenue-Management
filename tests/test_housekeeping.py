from fastapi.testclient import TestClient

from app.main import app
from app.database.database import SessionLocal
from app.models.room import Room

client = TestClient(app)


def test_create_housekeeping_task():
    response = client.post(
        "/housekeeping/",
        json={
            "room_id": 2,
            "assigned_to": "Staff 1",
            "notes": "Clean room after checkout"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["room_id"] == 2
    assert data["status"] == "DIRTY"
    assert data["assigned_to"] == "Staff 1"


def test_housekeeping_nonexistent_room():
    response = client.post(
        "/housekeeping/",
        json={
            "room_id": 99999,
            "assigned_to": "Staff 1",
            "notes": "Test"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Room not found"


def test_invalid_housekeeping_status():
    # Create task first
    response = client.post(
        "/housekeeping/",
        json={
            "room_id": 2,
            "assigned_to": "Staff 1",
            "notes": "Test cleaning"
        }
    )

    assert response.status_code == 200

    task_id = response.json()["id"]

    # Try invalid status
    response = client.put(
        f"/housekeeping/{task_id}",
        json={
            "status": "INVALID_STATUS"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid housekeeping status"


def test_housekeeping_cleaning_flow():
    # Create task
    response = client.post(
        "/housekeeping/",
        json={
            "room_id": 2,
            "assigned_to": "Staff 1",
            "notes": "Cleaning flow test"
        }
    )

    assert response.status_code == 200

    task_id = response.json()["id"]

    # Start cleaning
    response = client.put(
        f"/housekeeping/{task_id}",
        json={
            "status": "CLEANING_IN_PROGRESS"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CLEANING_IN_PROGRESS"

    # Check room became CLEANING
    db = SessionLocal()

    room = db.query(Room).filter(
        Room.id == 2
    ).first()

    assert room.status == "CLEANING"

    db.close()

    # Complete cleaning
    response = client.put(
        f"/housekeeping/{task_id}",
        json={
            "status": "CLEAN"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CLEAN"

    # Check room became AVAILABLE
    db = SessionLocal()

    room = db.query(Room).filter(
        Room.id == 2
    ).first()

    assert room.status == "AVAILABLE"

    db.close()

def test_get_nonexistent_housekeeping_task():
    response = client.get(
        "/housekeeping/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Housekeeping task not found"


def test_update_nonexistent_housekeeping_task():
    response = client.put(
        "/housekeeping/99999",
        json={
            "status": "CLEAN"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Housekeeping task not found"