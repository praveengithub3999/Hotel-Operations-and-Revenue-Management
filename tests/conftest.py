import os

os.environ["TESTING"] = "1"

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
from app.core.security import hash_password
from app.models.charge import Charge
@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    db = SessionLocal()

    try:
        # Remove old test reservations
        db.query(Payment).delete(synchronize_session = False)
        db.query(Invoice).delete(synchronize_session=False)
        db.query(Charge).delete(synchronize_session=False)

        # Reset room statuses
        db.query(Reservation).delete(synchronize_session=False)
        db.query(Room).update({
            Room.status: "AVAILABLE"
        },synchronize_session=False)

        db.commit()

        # Get or create hotel
        hotel = db.query(Hotel).filter(
            Hotel.name == "Test Hotel"
        ).first()

        if not hotel:
            hotel = Hotel(
                name="Test Hotel",
                address="Test Address",
                city="Hyderabad",
                contact_number="9000000000"
            )
            db.add(hotel)
            db.commit()
            db.refresh(hotel)

        # Get or create room type
        room_type = db.query(RoomType).filter(
            RoomType.name == "Deluxe",
            RoomType.hotel_id == hotel.id
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
            db.commit()
            db.refresh(room_type)

        # Get or create room 101
        room1 = db.query(Room).filter(
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

        # Get or create room 102
        room2 = db.query(Room).filter(
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

        # Get or create test guest
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

        db.commit()
                # Create test admin user
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

        # Create test staff user
        staff = db.query(User).filter(
            User.username == "staff1"
        ).first()

        if not staff:
            staff = User(
                username="staff1",
                email="staff@hotel.com",
                password_hash=hash_password("staff123"),
                role="STAFF",
                is_active=True
            )
            db.add(staff)

        # Remove test user so registration test starts clean
        db.query(User).filter(
            User.username == "testuser"
        ).delete(synchronize_session=False)

        db.commit()

        # Create a test reservation for payment tests
                # Create a test reservation for payment tests
        reservation = db.query(Reservation).filter(
            Reservation.special_requests == "Payment test reservation"
        ).first()

        if not reservation:
            reservation = Reservation(
                guest_id=guest.id,
                room_id=room1.id,
                check_in_date="2045-01-10",
                check_out_date="2045-01-12",
                number_of_guests=2,
                status="CONFIRMED",
                special_requests="Payment test reservation"
            )
            db.add(reservation)
            db.commit()
            db.refresh(reservation)

        # Create a test invoice
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

    finally:
        db.close()