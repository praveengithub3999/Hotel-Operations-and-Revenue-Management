
import uuid
from decimal import Decimal

from app.database.database import SessionLocal
from app.models.hotel import Hotel


def get_test_hotel_id():
    db = SessionLocal()

    try:
        hotel = db.query(Hotel).filter(
            Hotel.name == "Test Hotel"
        ).first()

        assert hotel is not None, "Test Hotel fixture was not found"
        return hotel.id
    finally:
        db.close()


def create_room_type_payload():
    unique_id = uuid.uuid4().hex[:10]

    return {
        "hotel_id": get_test_hotel_id(),
        "name": f"Room Type {unique_id}",
        "description": "Test room type",
        "capacity": 2,
        "base_price": 2500.00,
    }


def test_create_room_type_success(admin_client):
    payload = create_room_type_payload()

    response = admin_client.post("/room-types/", json=payload)

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["hotel_id"] == payload["hotel_id"]
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["capacity"] == payload["capacity"]
    assert Decimal(str(data["base_price"])) == Decimal("2500.00")
    assert "id" in data


def test_create_room_type_hotel_not_found(admin_client):
    payload = create_room_type_payload()
    payload["hotel_id"] = 999999

    response = admin_client.post("/room-types/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Hotel not found"


def test_create_duplicate_room_type(admin_client):
    payload = create_room_type_payload()

    first_response = admin_client.post("/room-types/", json=payload)
    assert first_response.status_code == 200, first_response.text

    second_response = admin_client.post("/room-types/", json=payload)

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "This room type already exists for this hotel"
    )


def test_create_room_type_duplicate_case_insensitive(admin_client):
    payload = create_room_type_payload()

    first_response = admin_client.post("/room-types/", json=payload)
    assert first_response.status_code == 200, first_response.text

    duplicate_payload = {
        **payload,
        "name": payload["name"].swapcase(),
    }

    second_response = admin_client.post(
        "/room-types/",
        json=duplicate_payload,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "This room type already exists for this hotel"
    )


def test_list_room_types(admin_client):
    response = admin_client.get("/room-types/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    assert any(
        room_type["name"] == "Deluxe"
        for room_type in response.json()
    )


def test_get_room_type_success(admin_client):
    payload = create_room_type_payload()

    create_response = admin_client.post("/room-types/", json=payload)
    assert create_response.status_code == 200, create_response.text

    room_type_id = create_response.json()["id"]

    response = admin_client.get(f"/room-types/{room_type_id}")

    assert response.status_code == 200, response.text
    assert response.json()["id"] == room_type_id
    assert response.json()["name"] == payload["name"]


def test_get_room_type_not_found(admin_client):
    response = admin_client.get("/room-types/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Room type not found"
