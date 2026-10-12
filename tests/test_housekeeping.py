
from app.database.database import SessionLocal
from app.models.room import Room


def test_create_housekeeping_task(admin_client):
    response = admin_client.post(
        "/housekeeping/",
        json={
            "room_id": 2,
            "assigned_to": "staff1",
            "notes": "Clean room after checkout"
        }
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["room_id"] == 2
    assert data["status"] == "DIRTY"
    assert data["assigned_to"] == "staff1"


def test_housekeeping_nonexistent_room(admin_client):
    response = admin_client.post(
        "/housekeeping/",
        json={
            "room_id": 99999,
            "assigned_to": "staff1",
            "notes": "Test"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Room not found"


def test_invalid_housekeeping_status(admin_client):
    response = admin_client.post(
        "/housekeeping/",
        json={
            "room_id": 2,
            "assigned_to": "staff1",
            "notes": "Test cleaning"
        }
    )

    assert response.status_code == 200, response.text
    task_id = response.json()["id"]

    response = admin_client.put(
        f"/housekeeping/{task_id}",
        json={"status": "INVALID_STATUS"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid housekeeping status"


def test_housekeeping_cleaning_flow(admin_client):
    from app.models.housekeeping import Housekeeping

    # Remove previous test tasks for room 2
    db = SessionLocal()
    try:
        db.query(Housekeeping).filter(
            Housekeeping.room_id == 2
        ).delete(synchronize_session=False)

        room = db.query(Room).filter(Room.id == 2).first()
        assert room is not None
        room.status = "AVAILABLE"
        db.commit()
    finally:
        db.close()

    # Create a fresh housekeeping task
    response = admin_client.post(
        "/housekeeping/",
        json={
            "room_id": 2,
            "assigned_to": "staff1",
            "notes": "Cleaning flow test"
        }
    )

    assert response.status_code == 200, response.text
    task_id = response.json()["id"]

    # Start cleaning
    response = admin_client.put(
        f"/housekeeping/{task_id}",
        json={"status": "CLEANING_IN_PROGRESS"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CLEANING_IN_PROGRESS"

    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == 2).first()
        assert room.status == "CLEANING"
    finally:
        db.close()

    # Finish cleaning
    response = admin_client.put(
        f"/housekeeping/{task_id}",
        json={"status": "CLEAN"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CLEAN"

    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == 2).first()
        assert room.status == "AVAILABLE"
    finally:
        db.close()

def test_get_nonexistent_housekeeping_task(admin_client):
    response = admin_client.get("/housekeeping/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Housekeeping task not found"


def test_update_nonexistent_housekeeping_task(admin_client):
    response = admin_client.put(
        "/housekeeping/99999",
        json={"status": "CLEAN"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Housekeeping task not found"
