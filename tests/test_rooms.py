
import uuid


def create_room_payload(admin_client):
    """Build room data using the hotel and room type from test fixtures."""
    from app.database.database import SessionLocal
    from app.models.hotel import Hotel
    from app.models.room_type import RoomType

    db = SessionLocal()

    try:
        hotel = db.query(Hotel).filter(
            Hotel.name == "Test Hotel"
        ).first()

        room_type = db.query(RoomType).filter(
            RoomType.name == "Deluxe"
        ).first()

        assert hotel is not None, "Test Hotel fixture was not found"
        assert room_type is not None, "Deluxe room type fixture was not found"

        return {
            "hotel_id": hotel.id,
            "room_type_id": room_type.id,
            "room_number": f"R{uuid.uuid4().hex[:8]}",
            "floor": 1,
        }
    finally:
        db.close()


def test_create_room_success(admin_client):
    payload = create_room_payload(admin_client)

    response = admin_client.post("/rooms/", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["room_number"] == payload["room_number"]
    assert data["hotel_id"] == payload["hotel_id"]
    assert data["room_type_id"] == payload["room_type_id"]


def test_create_room_hotel_not_found(admin_client):
    payload = create_room_payload(admin_client)
    payload["hotel_id"] = 999999

    response = admin_client.post("/rooms/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Hotel not found"


def test_create_room_room_type_not_found(admin_client):
    payload = create_room_payload(admin_client)
    payload["room_type_id"] = 999999

    response = admin_client.post("/rooms/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Room type not found"


def test_create_room_duplicate_room_number(admin_client):
    payload = create_room_payload(admin_client)

    first_response = admin_client.post("/rooms/", json=payload)
    assert first_response.status_code == 200, first_response.text

    second_response = admin_client.post("/rooms/", json=payload)

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Room number already exists in this hotel"
    )


def test_list_rooms(admin_client):
    response = admin_client.get("/rooms/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_room_success(admin_client):
    payload = create_room_payload(admin_client)

    create_response = admin_client.post("/rooms/", json=payload)
    assert create_response.status_code == 200, create_response.text

    room_id = create_response.json()["id"]

    response = admin_client.get(f"/rooms/{room_id}")

    assert response.status_code == 200, response.text
    assert response.json()["id"] == room_id
    assert response.json()["room_number"] == payload["room_number"]


def test_get_room_not_found(admin_client):
    response = admin_client.get("/rooms/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Room not found"
