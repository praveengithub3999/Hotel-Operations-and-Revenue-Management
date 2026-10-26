"""
Server CLI Script: Create Room
Allows administrators to directly create hotel rooms from the server terminal.
Usage:
    python scripts/create_room.py
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import SessionLocal
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.models.room import Room
from app.services.room_service import RoomService
from app.schemas.room import RoomCreate


def main():
    print("========================================")
    print("[HOTEL OPS] Create Room (Server CLI)")
    print("========================================")

    db = SessionLocal()
    try:
        # Check hotels
        hotels = db.query(Hotel).filter(Hotel.is_active == True).all()
        if not hotels:
            print("[INFO] No hotels found in the database.")
            create_hotel = input("Would you like to create a default hotel now? (y/n): ").strip().lower()
            if create_hotel == 'y':
                hotel_name = input("Hotel Name (e.g., Grand Palace): ").strip() or "Grand Palace"
                hotel_code = input("Hotel Code (e.g., GP01): ").strip().upper() or "GP01"
                new_hotel = Hotel(name=hotel_name, code=hotel_code, is_active=True)
                db.add(new_hotel)
                db.commit()
                db.refresh(new_hotel)
                hotels = [new_hotel]
                print(f"[OK] Hotel '{new_hotel.name}' (ID: {new_hotel.id}) created.")
            else:
                print("Cannot create a room without a hotel. Exiting.")
                return

        print("\nAvailable Hotels:")
        for h in hotels:
            print(f"  [{h.id}] {h.name} (Code: {h.code})")

        hotel_id_input = input(f"Enter Hotel ID [{hotels[0].id}]: ").strip()
        hotel_id = int(hotel_id_input) if hotel_id_input else hotels[0].id

        # Check room types for this hotel
        room_types = db.query(RoomType).filter(RoomType.hotel_id == hotel_id).all()
        if not room_types:
            print(f"\n[INFO] No room types found for Hotel ID {hotel_id}.")
            create_rt = input("Would you like to create a room type now? (y/n): ").strip().lower()
            if create_rt == 'y':
                rt_name = input("Room Type Name (e.g., Deluxe Suite): ").strip() or "Deluxe Suite"
                base_price = input("Base Price per night (e.g., 2500.00): ").strip() or "2500.00"
                capacity = input("Capacity (e.g., 2): ").strip() or "2"
                new_rt = RoomType(
                    hotel_id=hotel_id,
                    name=rt_name,
                    base_price=float(base_price),
                    capacity=int(capacity)
                )
                db.add(new_rt)
                db.commit()
                db.refresh(new_rt)
                room_types = [new_rt]
                print(f"[OK] Room Type '{new_rt.name}' (ID: {new_rt.id}) created.")
            else:
                print("Cannot create a room without a room type. Exiting.")
                return

        print("\nAvailable Room Types:")
        for rt in room_types:
            print(f"  [{rt.id}] {rt.name} - Rs. {rt.base_price}/night (Capacity: {rt.capacity})")

        rt_id_input = input(f"Enter Room Type ID [{room_types[0].id}]: ").strip()
        room_type_id = int(rt_id_input) if rt_id_input else room_types[0].id

        room_number = input("\nEnter Room Number (e.g., 101): ").strip()
        if not room_number:
            print("[ERROR] Room number cannot be empty.")
            return

        floor_input = input("Enter Floor Number (e.g., 1): ").strip() or "1"
        floor = int(floor_input)

        service = RoomService(db)
        room_payload = RoomCreate(
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            room_number=room_number,
            floor=floor
        )

        created_room = service.create_room(room_payload)
        print("\n[SUCCESS] Room created successfully from the server:")
        print(f"   ID:          {created_room.id}")
        print(f"   Room Number: {created_room.room_number}")
        print(f"   Floor:       {created_room.floor}")
        print(f"   Status:      {created_room.status}")
        print(f"   Hotel ID:    {created_room.hotel_id}")
        print(f"   Type ID:     {created_room.room_type_id}")

    except Exception as e:
        print(f"\n[ERROR] Error creating room: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
