from app.database.database import SessionLocal
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.models.room import Room
from app.models.guest import Guest


db = SessionLocal()

try:
    hotel = Hotel(
        name="Test Hotel",
        address="Test Address",
        city = "Hyderabad",
        contact_number="9000000000"
    )
    db.add(hotel)
    db.commit()
    db.refresh(hotel)

    room_type = RoomType(
        hotel_id = hotel.id,
        name="Deluxe",
        description="Test deluxe room",
        capacity=2,
        base_price=3000
    )
    db.add(room_type)
    db.commit()
    db.refresh(room_type)

    room = Room(
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        room_number="101",
        floor=1,
        status="AVAILABLE"
    )
    db.add(room)

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

    print("Test data created successfully!")

finally:
    db.close()