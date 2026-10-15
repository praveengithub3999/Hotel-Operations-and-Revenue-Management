from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.repositories.guest_repository import GuestRepository
from app.schemas.guest import GuestCreate


class GuestService:
    def __init__(self, db: Session):
        self.db = db
        self.guest_repo = GuestRepository(db)

    def create_guest(self, data: GuestCreate) -> Guest:
        if data.email:
            existing_email = self.guest_repo.find_by_email(data.email)
            if existing_email:
                raise HTTPException(
                    status_code=409,
                    detail="A guest with this email already exists"
                )

        if data.id_reference:
            existing_id = self.guest_repo.find_by_id_reference(data.id_reference)
            if existing_id:
                raise HTTPException(
                    status_code=409,
                    detail="A guest with this ID reference already exists"
                )

        guest = Guest(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            address=data.address,
            id_type=data.id_type,
            id_reference=data.id_reference,
            emergency_contact=data.emergency_contact
        )
        return self.guest_repo.create(guest)

    def get_guests(self) -> List[Guest]:
        return self.guest_repo.get_all()

    def get_guest_by_id(self, guest_id: int) -> Guest:
        guest = self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise HTTPException(status_code=404, detail="Guest not found")
        return guest
