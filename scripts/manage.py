"""
Unified Server Management CLI
Provides server administrators with direct commands to create and inspect hotels, rooms, and guests.

Usage:
    python scripts/manage.py create-admin
    python scripts/manage.py create-room
    python scripts/manage.py create-guest
    python scripts/manage.py list-rooms
    python scripts/manage.py list-guests
    python scripts/manage.py seed-demo
"""

import os
import sys
import argparse

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import SessionLocal
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.models.room import Room
from app.models.guest import Guest
from app.models.user import User
from app.core.security import hash_password
from app.services.room_service import RoomService
from app.services.guest_service import GuestService
from app.schemas.room import RoomCreate
from app.schemas.guest import GuestCreate


def cmd_list_rooms():
    db = SessionLocal()
    try:
        rooms = db.query(Room).all()
        print(f"\n[HOTEL] Total Rooms in Database: {len(rooms)}")
        print("-" * 55)
        print(f"{'ID':<6}{'Room No':<12}{'Floor':<8}{'Status':<15}{'Hotel ID':<10}")
        print("-" * 55)
        for r in rooms:
            print(f"{r.id:<6}{r.room_number:<12}{r.floor:<8}{r.status:<15}{r.hotel_id:<10}")
        print("-" * 55)
    finally:
        db.close()


def cmd_list_guests():
    db = SessionLocal()
    try:
        guests = db.query(Guest).all()
        print(f"\n[GUESTS] Total Guests in Database: {len(guests)}")
        print("-" * 80)
        print(f"{'ID':<6}{'Name':<22}{'Email':<30}{'Phone':<15}")
        print("-" * 80)
        for g in guests:
            name = f"{g.first_name} {g.last_name}"
            print(f"{g.id:<6}{name:<22}{g.email:<30}{g.phone:<15}")
        print("-" * 80)
    finally:
        db.close()


def cmd_seed_demo():
    print("\n[SEED] Seeding demo hotels, room types, rooms, and guests...")
    db = SessionLocal()
    try:
        # Hotel
        hotel = db.query(Hotel).filter(Hotel.code == "GP01").first()
        if not hotel:
            hotel = Hotel(name="Grand Palace Hotel & Resort", code="GP01", address="100 Luxury Avenue", phone="1800123456", email="info@grandpalace.com", is_active=True)
            db.add(hotel)
            db.commit()
            db.refresh(hotel)
            print(f"  + Hotel created: {hotel.name} (Code: {hotel.code})")

        # Room Types
        types_data = [
            ("Standard Deluxe", 2500.00, 2),
            ("Executive Suite", 5000.00, 3),
            ("Presidential Penthouse", 12000.00, 4)
        ]
        created_types = []
        for name, price, cap in types_data:
            rt = db.query(RoomType).filter(RoomType.hotel_id == hotel.id, RoomType.name == name).first()
            if not rt:
                rt = RoomType(hotel_id=hotel.id, name=name, base_price=price, capacity=cap, description=f"Premium {name}")
                db.add(rt)
                db.commit()
                db.refresh(rt)
                print(f"  + Room Type created: {rt.name} (Rs. {rt.base_price}/night)")
            created_types.append(rt)

        # Rooms
        sample_rooms = [
            ("101", 1, created_types[0].id),
            ("102", 1, created_types[0].id),
            ("201", 2, created_types[1].id),
            ("202", 2, created_types[1].id),
            ("301", 3, created_types[2].id)
        ]
        for num, flr, t_id in sample_rooms:
            r = db.query(Room).filter(Room.hotel_id == hotel.id, Room.room_number == num).first()
            if not r:
                r = Room(hotel_id=hotel.id, room_type_id=t_id, room_number=num, floor=flr, status="AVAILABLE")
                db.add(r)
                db.commit()
                print(f"  + Room created: Room {num} (Floor {flr})")

        # Sample Guests
        sample_guests = [
            ("Praveen", "Kumar", "praveen.kumar@example.com", "9876543211", "PASSPORT", "PASS-IN-987"),
            ("Aarav", "Sharma", "aarav.sharma@example.com", "9876543212", "AADHAAR", "AADHAAR-8765"),
            ("Sophia", "Taylor", "sophia.taylor@example.com", "9876543213", "DRIVING_LICENSE", "DL-US-4567")
        ]
        for fn, ln, em, ph, idt, idref in sample_guests:
            g = db.query(Guest).filter(Guest.email == em).first()
            if not g:
                g = Guest(first_name=fn, last_name=ln, email=em, phone=ph, address="City Center", id_type=idt, id_reference=idref, emergency_contact=ph)
                db.add(g)
                db.commit()
                print(f"  + Guest created: {fn} {ln} ({em})")

        print("\n[SUCCESS] Demo seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during demo seeding: {e}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Hotel Operations Server Admin CLI")
    parser.add_argument(
        "action",
        choices=["create-admin", "create-room", "create-guest", "list-rooms", "list-guests", "seed-demo"],
        help="Administrative action to perform"
    )

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.action == "create-admin":
        from scripts.create_admin import main as run_create_admin
        run_create_admin()
    elif args.action == "create-room":
        from scripts.create_room import main as run_create_room
        run_create_room()
    elif args.action == "create-guest":
        from scripts.create_guest import main as run_create_guest
        run_create_guest()
    elif args.action == "list-rooms":
        cmd_list_rooms()
    elif args.action == "list-guests":
        cmd_list_guests()
    elif args.action == "seed-demo":
        cmd_seed_demo()


if __name__ == "__main__":
    main()
