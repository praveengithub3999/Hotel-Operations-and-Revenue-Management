
import uuid


def test_create_guest_success(admin_client):
    unique_id = uuid.uuid4().hex
    email = f"ravi_{unique_id}@example.com"

    response = admin_client.post(
        "/guests/",
        json={
            "first_name": "Ravi",
            "last_name": "Kumar",
            "email": email,
            "phone": "9000000011",
            "address": "Hyderabad",
            "id_type": "PASSPORT",
            "id_reference": f"PASS-{unique_id}",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["first_name"] == "Ravi"
    assert data["last_name"] == "Kumar"
    assert data["email"] == email


def test_create_guest_duplicate_email(admin_client):
    unique_id = uuid.uuid4().hex

    guest_data = {
        "first_name": "Ravi",
        "last_name": "Kumar",
        "email": f"duplicate_{unique_id}@example.com",
        "phone": "9000000012",
        "address": "Hyderabad",
        "id_type": "PASSPORT",
        "id_reference": f"PASS-{unique_id}-1",
    }

    first_response = admin_client.post(
        "/guests/",
        json=guest_data,
    )

    assert first_response.status_code == 200, first_response.text

    second_response = admin_client.post(
        "/guests/",
        json=guest_data,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A guest with this email already exists"
    )


def test_create_guest_duplicate_id_reference(admin_client):
    unique_id = uuid.uuid4().hex
    shared_reference = f"PASS-{unique_id}"

    first_response = admin_client.post(
        "/guests/",
        json={
            "first_name": "Guest",
            "last_name": "One",
            "email": f"guest_one_{unique_id}@example.com",
            "phone": "9000000013",
            "address": "Hyderabad",
            "id_type": "PASSPORT",
            "id_reference": shared_reference,
        },
    )

    assert first_response.status_code == 200, first_response.text

    second_response = admin_client.post(
        "/guests/",
        json={
            "first_name": "Guest",
            "last_name": "Two",
            "email": f"guest_two_{unique_id}@example.com",
            "phone": "9000000014",
            "address": "Hyderabad",
            "id_type": "PASSPORT",
            "id_reference": shared_reference,
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A guest with this ID reference already exists"
    )


def test_list_guests(admin_client):
    response = admin_client.get("/guests/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    assert any(
        guest["email"] == "testguest@test.com"
        for guest in response.json()
    )


def test_get_guest_success(admin_client):
    list_response = admin_client.get("/guests/")

    assert list_response.status_code == 200

    guest = next(
        (
            item
            for item in list_response.json()
            if item["email"] == "testguest@test.com"
        ),
        None,
    )

    assert guest is not None

    response = admin_client.get(f"/guests/{guest['id']}")

    assert response.status_code == 200, response.text
    assert response.json()["id"] == guest["id"]
    assert response.json()["email"] == "testguest@test.com"


def test_get_guest_not_found(admin_client):
    response = admin_client.get("/guests/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Guest not found"
