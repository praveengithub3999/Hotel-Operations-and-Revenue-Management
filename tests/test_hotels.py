
import uuid


def create_hotel_payload():
    unique_id = uuid.uuid4().hex[:10]

    return {
        "name": f"Test Hotel {unique_id}",
        "address": "123 Test Street",
        "city": f"Hyderabad {unique_id}",
        "contact_number": "9000000011",
    }


def test_create_hotel_success(admin_client):
    payload = create_hotel_payload()

    response = admin_client.post("/hotels/", json=payload)

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["name"] == payload["name"]
    assert data["address"] == payload["address"]
    assert data["city"] == payload["city"]
    assert data["contact_number"] == payload["contact_number"]
    assert "id" in data


def test_create_duplicate_hotel_same_city(admin_client):
    payload = create_hotel_payload()

    first_response = admin_client.post("/hotels/", json=payload)
    assert first_response.status_code == 200, first_response.text

    second_response = admin_client.post("/hotels/", json=payload)

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A hotel with this name already exists in this city"
    )


def test_create_hotel_duplicate_case_insensitive(admin_client):
    payload = create_hotel_payload()

    first_response = admin_client.post("/hotels/", json=payload)
    assert first_response.status_code == 200, first_response.text

    duplicate_payload = {
        "name": payload["name"].swapcase(),
        "address": "456 Different Street",
        "city": payload["city"].swapcase(),
        "contact_number": "9000000012",
    }

    second_response = admin_client.post(
        "/hotels/",
        json=duplicate_payload,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A hotel with this name already exists in this city"
    )


def test_create_hotel_trims_whitespace(admin_client):
    payload = create_hotel_payload()
    payload["name"] = f"  {payload['name']}  "
    payload["address"] = f"  {payload['address']}  "
    payload["city"] = f"  {payload['city']}  "
    payload["contact_number"] = f"  {payload['contact_number']}  "

    response = admin_client.post("/hotels/", json=payload)

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["name"] == payload["name"].strip()
    assert data["address"] == payload["address"].strip()
    assert data["city"] == payload["city"].strip()
    assert data["contact_number"] == payload["contact_number"].strip()


def test_list_hotels(admin_client):
    response = admin_client.get("/hotels/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    hotel_names = [hotel["name"] for hotel in response.json()]
    assert "Test Hotel" in hotel_names


def test_get_hotel_success(admin_client):
    payload = create_hotel_payload()

    create_response = admin_client.post("/hotels/", json=payload)
    assert create_response.status_code == 200, create_response.text

    hotel_id = create_response.json()["id"]

    response = admin_client.get(f"/hotels/{hotel_id}")

    assert response.status_code == 200, response.text
    assert response.json()["id"] == hotel_id
    assert response.json()["name"] == payload["name"]


def test_get_hotel_not_found(admin_client):
    response = admin_client.get("/hotels/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Hotel not found"


def test_get_hotel_invalid_zero_id(admin_client):
    response = admin_client.get("/hotels/0")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Hotel ID must be greater than zero"
    )


def test_get_hotel_negative_id(admin_client):
    response = admin_client.get("/hotels/-1")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Hotel ID must be greater than zero"
    )
