import uuid
from datetime import date, timedelta
from decimal import Decimal
from app.database.database import SessionLocal
from app.models.room import Room
from app.models.reservation import Reservation
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.hotel import Hotel
from app.models.room_type import RoomType


def test_put_room_update(admin_client):
    """Test PUT /rooms/{id} updates room details."""
    response = admin_client.get("/rooms/")
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) > 0
    target_room = rooms[0]

    update_payload = {"floor": 3, "status": "AVAILABLE"}
    put_res = admin_client.put(f"/rooms/{target_room['id']}", json=update_payload)
    assert put_res.status_code == 200, put_res.text
    updated = put_res.json()
    assert updated["floor"] == 3
    assert updated["status"] == "AVAILABLE"


def test_get_rooms_availability_query(admin_client):
    """Test GET /rooms/availability with date range filters."""
    check_in = date.today() + timedelta(days=200)
    check_out = check_in + timedelta(days=3)

    response = admin_client.get(
        "/rooms/availability",
        params={
            "check_in_date": str(check_in),
            "check_out_date": str(check_out)
        }
    )
    assert response.status_code == 200, response.text
    available_rooms = response.json()
    assert isinstance(available_rooms, list)
    assert len(available_rooms) > 0


def test_dynamic_pricing_calculation(admin_client):
    """Test dynamic pricing calculation endpoint."""
    response = admin_client.get("/rooms/1/pricing", params={"stay_date": "2026-10-17"})  # Saturday in peak month
    assert response.status_code == 200, response.text
    data = response.json()
    assert "dynamic_price" in data
    assert data["is_weekend"] is True
    assert data["is_peak_month"] is True


def prepare_room(room_id, check_in, check_out):
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            room.status = "AVAILABLE"
            room.housekeeping_status = "CLEAN"
        db.query(Reservation).filter(
            Reservation.room_id == room_id,
            Reservation.check_in_date < check_out,
            Reservation.check_out_date > check_in,
            Reservation.status.in_(["CONFIRMED", "CHECKED_IN"])
        ).update({Reservation.status: "CANCELLED"}, synchronize_session=False)
        db.commit()
    finally:
        db.close()


def test_put_reservation_update(admin_client):
    """Test PUT /reservations/{id} allows modifying stay details."""
    check_in = date.today() + timedelta(days=220)
    check_out = check_in + timedelta(days=2)
    prepare_room(1, check_in, check_out + timedelta(days=5))

    create_res = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
            "number_of_guests": 2,
            "special_requests": "Original request"
        }
    )
    assert create_res.status_code == 200, create_res.text
    res_id = create_res.json()["id"]

    # Modify reservation
    new_check_out = check_in + timedelta(days=4)
    update_res = admin_client.put(
        f"/reservations/{res_id}",
        json={
            "check_out_date": str(new_check_out),
            "special_requests": "Updated: extra towels and late checkout"
        }
    )
    assert update_res.status_code == 200, update_res.text
    data = update_res.json()
    assert data["check_out_date"] == str(new_check_out)
    assert "extra towels" in data["special_requests"]


def test_cancellation_policy_tiers(admin_client):
    """Test cancellation policy tiers (>7 days = 100% refund eligible)."""
    check_in = date.today() + timedelta(days=15)
    check_out = check_in + timedelta(days=2)
    prepare_room(1, check_in, check_out)

    create_res = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 1,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
            "number_of_guests": 1,
            "special_requests": "Cancellation tier test"
        }
    )
    assert create_res.status_code == 200, create_res.text
    res_id = create_res.json()["id"]

    cancel_res = admin_client.delete(f"/reservations/{res_id}")
    assert cancel_res.status_code == 200, cancel_res.text
    data = cancel_res.json()
    assert data["status"] == "CANCELLED"
    assert "cancellation_policy" in data
    assert data["cancellation_policy"]["refund_tier"] == "FULL_REFUND"
    assert data["cancellation_policy"]["eligible_refund_percentage"] == 100.0


def test_no_shows_process(admin_client):
    """Test processing overdue confirmed reservations to NO_SHOW."""
    response = admin_client.post("/reservations/no-shows/process")
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_update_room_housekeeping_status_direct(admin_client):
    """Test PUT /rooms/{id}/housekeeping-status (Member 2 API requirement)."""
    response = admin_client.put("/rooms/1/housekeeping-status", params={"status": "CLEAN"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["room_id"] == 1
    assert data["housekeeping_status"] == "CLEAN"
    assert data["room_status"] == "AVAILABLE"


def test_staff_assignments_flow(admin_client):
    """Test POST & GET /staff/assignments for room and maintenance."""
    assign_res = admin_client.post(
        "/staff/assignments/",
        json={
            "staff_username": "staff1",
            "staff_role": "HOUSEKEEPING",
            "assigned_entity": "ROOM",
            "entity_id": 1,
            "notes": "Morning room inspection"
        }
    )
    # staff1 is registered as RECEPTIONIST in conftest; admin is admin.
    # We test with admin or a housekeeping staff.
    if assign_res.status_code == 400:
        # Assign admin who has role ADMIN
        assign_res = admin_client.post(
            "/staff/assignments/",
            json={
                "staff_username": "admin",
                "staff_role": "HOUSEKEEPING",
                "assigned_entity": "ROOM",
                "entity_id": 1,
                "notes": "Admin room check"
            }
        )
    assert assign_res.status_code == 200, assign_res.text
    data = assign_res.json()
    assert data["assigned_entity"] == "ROOM"

    list_res = admin_client.get("/staff/assignments/")
    assert list_res.status_code == 200, list_res.text
    assert len(list_res.json()) > 0


def test_maintenance_sla_and_alias(admin_client):
    """Test /maintenance-requests alias and SLA endpoint."""
    create_res = admin_client.post(
        "/maintenance-requests/",
        json={
            "room_id": 1,
            "issue": "AC leakage and high temperature",
            "priority": "CRITICAL",
            "category": "HVAC",
            "description": "Room AC not cooling"
        }
    )
    assert create_res.status_code == 200, create_res.text
    maint_id = create_res.json()["id"]

    sla_res = admin_client.get(f"/maintenance/{maint_id}/sla")
    assert sla_res.status_code == 200, sla_res.text
    sla_data = sla_res.json()
    assert sla_data["priority"] == "CRITICAL"
    assert sla_data["sla_target_hours"] == 2
    assert "deadline" in sla_data


def test_discounts_api(admin_client):
    """Test POST /discounts and GET /discounts (Member 3 API requirement)."""
    code = f"DISC_{uuid.uuid4().hex[:6]}"
    create_res = admin_client.post(
        "/discounts/",
        json={
            "code": code,
            "discount_type": "PERCENTAGE",
            "value": "15.00",
            "description": "15% corporate partner discount"
        }
    )
    assert create_res.status_code == 200, create_res.text
    data = create_res.json()
    assert data["code"] == code.upper()
    assert Decimal(str(data["value"])) == Decimal("15.00")

    get_res = admin_client.get("/discounts/")
    assert get_res.status_code == 200, get_res.text
    assert any(d["code"] == code.upper() for d in get_res.json())


def test_duplicate_charge_prevention(admin_client):
    """Test duplicate charge prevention (PDF Section 26 requirement)."""
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == 2).first()
        if room:
            room.status = "AVAILABLE"
            db.commit()
    finally:
        db.close()

    check_in = date(2048, 5, 10)
    check_out = date(2048, 5, 12)
    res = admin_client.post(
        "/reservations/",
        json={
            "guest_id": 1,
            "room_id": 2,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
            "number_of_guests": 1,
            "special_requests": "Duplicate charge test"
        }
    )
    assert res.status_code == 200, res.text
    res_id = res.json()["id"]

    first_charge = admin_client.post(
        "/charges/",
        json={
            "reservation_id": res_id,
            "charge_type": "LAUNDRY",
            "description": "Dry cleaning suit",
            "quantity": 1,
            "unit_price": "500.00"
        }
    )
    assert first_charge.status_code == 200, first_charge.text

    # Attempt same charge again without allow_duplicate flag
    dup_charge = admin_client.post(
        "/charges/",
        json={
            "reservation_id": res_id,
            "charge_type": "LAUNDRY",
            "description": "Dry cleaning suit",
            "quantity": 1,
            "unit_price": "500.00"
        }
    )
    assert dup_charge.status_code == 409
    assert "Duplicate charge detected" in dup_charge.json()["detail"]


def test_room_performance_report(admin_client):
    """Test GET /reports/room-performance (PDF Page 10 & 24 requirement)."""
    response = admin_client.get("/reports/room-performance")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "performance" in data
    assert isinstance(data["performance"], list)
    if data["performance"]:
        item = data["performance"][0]
        assert "room_type" in item
        assert "number_of_bookings" in item
        assert "revenue" in item
        assert "occupancy_percentage" in item
        assert "average_rate" in item


def test_guest_feedback_mongodb(admin_client):
    """Test storing and reading guest feedback in MongoDB (Section 18)."""
    db = SessionLocal()
    try:
        res = db.query(Reservation).first()
        res_id = res.id if res else 1
    finally:
        db.close()

    response = admin_client.post(
        "/feedback/",
        json={
            "reservation_id": res_id,
            "rating": 5,
            "categories": {
                "room": 5,
                "service": 4,
                "cleanliness": 5
            },
            "comment": "Exceptional stay and pristine rooms!"
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["rating"] == 5

    get_fb = admin_client.get(f"/feedback/{res_id}")
    assert get_fb.status_code == 200, get_fb.text


def test_auth_me_endpoint(admin_client):
    """Test GET /auth/me returns authenticated user details."""
    response = admin_client.get("/auth/me")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "ADMIN"
