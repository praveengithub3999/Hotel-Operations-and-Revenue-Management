
import os
from datetime import date

# Load test settings before importing the application database.
from dotenv import load_dotenv

os.environ["TESTING"] = "1"
load_dotenv(".env.test", override=True)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is missing from .env.test. "
        "Configure the dedicated test database before running pytest."
    )

# Make sure the application database module uses the test URL.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest

from app.database.database import SessionLocal
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.models.room import Room
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.user import User
from app.models.charge import Charge
from app.models.refund import Refund
from app.models.service_request import ServiceRequest
from app.core.security import hash_password


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    db = SessionLocal()

    try:
        # Delete dependent records before their parent records.
        db.query(ServiceRequest).delete(synchronize_session=False)
        db.query(Refund).delete(synchronize_session=False)
        db.query(Payment).delete(synchronize_session=False)
        db.query(Charge).delete(synchronize_session=False)
        db.query(Invoice).delete(synchronize_session=False)
        db.query(Reservation).delete(synchronize_session=False)

        # Reset room statuses.
        db.query(Room).update(
            {Room.status: "AVAILABLE"},
            synchronize_session=False
        )

        db.commit()

        # Get or create test hotel.
        hotel = db.query(Hotel).filter(
            Hotel.name == "Test Hotel",
            Hotel.city == "Hyderabad"
        ).first()

        if not hotel:
            hotel = Hotel(
                name="Test Hotel",
                address="Test Address",
                city="Hyderabad",
                contact_number="9000000000"
            )
            db.add(hotel)
            db.flush()

        # Get or create test room type.
        room_type = db.query(RoomType).filter(
            RoomType.hotel_id == hotel.id,
            RoomType.name == "Deluxe"
        ).first()

        if not room_type:
            room_type = RoomType(
                hotel_id=hotel.id,
                name="Deluxe",
                description="Test deluxe room",
                capacity=2,
                base_price=3000
            )
            db.add(room_type)
            db.flush()

        # Get or create room 101.
        room1 = db.query(Room).filter(
            Room.hotel_id == hotel.id,
            Room.room_number == "101"
        ).first()

        if not room1:
            room1 = Room(
                hotel_id=hotel.id,
                room_type_id=room_type.id,
                room_number="101",
                floor=1,
                status="AVAILABLE"
            )
            db.add(room1)
            db.flush()

        # Get or create room 102.
        room2 = db.query(Room).filter(
            Room.hotel_id == hotel.id,
            Room.room_number == "102"
        ).first()

        if not room2:
            room2 = Room(
                hotel_id=hotel.id,
                room_type_id=room_type.id,
                room_number="102",
                floor=1,
                status="AVAILABLE"
            )
            db.add(room2)
            db.flush()

        # Get or create test guest.
        guest = db.query(Guest).filter(
            Guest.email == "testguest@test.com"
        ).first()

        if not guest:
            guest = Guest(
                first_name="Test",
                last_name="Guest",
                email="testguest@test.com",
                phone="9000000001",
                address="Hyderabad",
                id_type="PASSPORT",
                id_reference="TEST123"
            )
            db.add(guest)
            db.flush()

        # Get or create ADMIN account.
        admin = db.query(User).filter(
            User.username == "admin"
        ).first()

        if not admin:
            admin = User(
                username="admin",
                email="admin@hotel.com",
                password_hash=hash_password("admin123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin)

        # Get or create a valid non-admin account.
        staff = db.query(User).filter(
            User.username == "staff1"
        ).first()

        if not staff:
            staff = User(
                username="staff1",
                email="staff@hotel.com",
                password_hash=hash_password("staff123"),
                role="RECEPTIONIST",
                is_active=True
            )
            db.add(staff)

        # Ensure the registration test starts with a fresh test user.
        db.query(User).filter(
            User.username == "testuser"
        ).delete(synchronize_session=False)

        db.flush()

        # Create the payment-test reservation.
        reservation = db.query(Reservation).filter(
            Reservation.special_requests == "Payment test reservation"
        ).first()

        if not reservation:
            reservation = Reservation(
                guest_id=guest.id,
                room_id=room1.id,
                check_in_date=date(2045, 1, 10),
                check_out_date=date(2045, 1, 12),
                number_of_guests=2,
                status="CONFIRMED",
                special_requests="Payment test reservation"
            )
            db.add(reservation)
            db.flush()

        # Create its test invoice.
        invoice = db.query(Invoice).filter(
            Invoice.reservation_id == reservation.id
        ).first()

        if not invoice:
            invoice = Invoice(
                reservation_id=reservation.id,
                subtotal=5000,
                discount=0,
                tax=900,
                total=5900,
                status="UNPAID"
            )
            db.add(invoice)

        db.commit()
        yield

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_client(client):
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert response.status_code == 200, (
        f"Admin login failed: {response.status_code} "
        f"{response.text}"
    )

    token = response.json()["access_token"]
    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    yield client

    client.headers.pop("Authorization", None)


@pytest.fixture
def receptionist_client(client):
    response = client.post(
        "/auth/login",
        json={
            "username": "staff1",
            "password": "staff123"
        }
    )

    assert response.status_code == 200, (
        f"Receptionist login failed: {response.status_code} "
        f"{response.text}"
    )

    token = response.json()["access_token"]
    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    yield client

    client.headers.pop("Authorization", None)
