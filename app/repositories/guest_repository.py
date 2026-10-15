from typing import Optional
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.repositories.base import BaseRepository


class GuestRepository(BaseRepository[Guest]):
    def __init__(self, db: Session):
        super().__init__(Guest, db)

    def find_by_email(self, email: str) -> Optional[Guest]:
        return self.db.query(Guest).filter(Guest.email == email).first()

    def find_by_id_reference(self, id_reference: str) -> Optional[Guest]:
        return self.db.query(Guest).filter(Guest.id_reference == id_reference).first()
