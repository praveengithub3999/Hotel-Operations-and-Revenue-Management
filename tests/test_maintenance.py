from app.database.database import SessionLocal
from app.models.room import Room
from app.models.maintenance import Maintenance


def test_create_maintenance_request(admin_client):
    response = admin_client.post(
        "/maintenance/",
        json={
            "room_id": 2,
            "issue": "Air conditioner not working",
            "assigned_to": "staff1",
            "notes": "Check the AC unit"
        }
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["room_id"] == 2
    assert data["issue"] == "Air conditioner not working"
    assert data["status"] == "OPEN"
    assert data["assigned_to"] == "staff1"


def test_create_maintenance_for_nonexistent_room(admin_client):
    response = admin_client.post(
        "/maintenance/",
        json={
            "room_id": 99999,
            "issue": "Broken light",
            "notes": "Test missing room"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Room not found"


def test_update_maintenance_status(admin_client):
    create_response = admin_client.post(
        "/maintenance/",
        json={
            "room_id": 2,
            "issue": "Bathroom tap leaking",
            "assigned_to": "staff1"
        }
    )

    assert create_response.status_code == 200, create_response.text
    maintenance_id = create_response.json()["id"]

    response = admin_client.put(
        f"/maintenance/{maintenance_id}",
        json={
            "status": "IN_PROGRESS",
            "notes": "Repair work started"
        }
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["notes"] == "Repair work started"

    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == 2).first()
        assert room is not None
        assert room.status == "MAINTENANCE"
    finally:
        db.close()


def test_invalid_maintenance_status(admin_client):
    create_response = admin_client.post(
        "/maintenance/",
        json={
            "room_id": 2,
            "issue": "Faulty door lock"
        }
    )

    assert create_response.status_code == 200, create_response.text
    maintenance_id = create_response.json()["id"]

    response = admin_client.put(
        f"/maintenance/{maintenance_id}",
        json={"status": "INVALID_STATUS"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid maintenance status"


def test_get_nonexistent_maintenance(admin_client):
    response = admin_client.get("/maintenance/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Maintenance record not found"


def test_update_nonexistent_maintenance(admin_client):
    response = admin_client.put(
        "/maintenance/99999",
        json={"status": "RESOLVED"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Maintenance record not found"


def test_resolve_maintenance_request(admin_client):
    create_response = admin_client.post(
        "/maintenance/",
        json={
            "room_id": 2,
            "issue": "Broken ceiling fan",
            "assigned_to": "staff1"
        }
    )

    assert create_response.status_code == 200, create_response.text
    maintenance_id = create_response.json()["id"]

    response = admin_client.put(
        f"/maintenance/{maintenance_id}",
        json={
            "status": "RESOLVED",
            "notes": "Fan repaired successfully"
        }
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["status"] == "RESOLVED"
    assert data["resolved_at"] is not None
    assert data["notes"] == "Fan repaired successfully"
