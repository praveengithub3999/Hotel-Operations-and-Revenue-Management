"""
Server CLI Script: Create Guest
Allows administrators to directly register guest profiles from the server terminal.
Usage:
    python scripts/create_guest.py
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import SessionLocal
from app.services.guest_service import GuestService
from app.schemas.guest import GuestCreate


def main():
    print("========================================")
    print("[GUEST REGISTRY] Create Guest (Server CLI)")
    print("========================================")

    db = SessionLocal()
    try:
        first_name = input("First Name (required): ").strip()
        if not first_name:
            print("[ERROR] First name is required.")
            return

        last_name = input("Last Name (required): ").strip()
        if not last_name:
            print("[ERROR] Last name is required.")
            return

        email = input("Email (e.g. guest@example.com): ").strip().lower()
        if not email:
            print("[ERROR] Email is required.")
            return

        phone = input("Phone Number (e.g. 9876543210): ").strip()
        if not phone:
            print("[ERROR] Phone number is required.")
            return

        address = input("Address: ").strip() or "Not specified"

        print("\nID Proof Types: PASSPORT, DRIVING_LICENSE, NATIONAL_ID, AADHAAR, VOTER_ID")
        id_type = input("ID Type [PASSPORT]: ").strip().upper() or "PASSPORT"
        id_reference = input("ID Proof Number / Reference: ").strip() or f"ID-{phone}"
        emergency_contact = input("Emergency Contact Number: ").strip() or phone

        service = GuestService(db)
        guest_payload = GuestCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            id_type=id_type,
            id_reference=id_reference,
            emergency_contact=emergency_contact
        )

        created_guest = service.create_guest(guest_payload)
        print("\n[SUCCESS] Guest registered successfully from the server:")
        print(f"   Guest ID:          {created_guest.id}")
        print(f"   Full Name:         {created_guest.first_name} {created_guest.last_name}")
        print(f"   Email:             {created_guest.email}")
        print(f"   Phone:             {created_guest.phone}")
        print(f"   ID Type:           {created_guest.id_type} ({created_guest.id_reference})")
        print(f"   Emergency Contact: {created_guest.emergency_contact}")

    except Exception as e:
        print(f"\n[ERROR] Error creating guest: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
