from typing import List
from sqlalchemy.orm import Session

from app.models.staff_assignment import StaffAssignment
from app.repositories.base import BaseRepository


class StaffAssignmentRepository(BaseRepository[StaffAssignment]):
    def __init__(self, db: Session):
        super().__init__(StaffAssignment, db)

    def get_by_staff(self, username: str) -> List[StaffAssignment]:
        return self.db.query(StaffAssignment).filter(
            StaffAssignment.staff_username == username
        ).all()

    def get_by_entity(self, entity_type: str, entity_id: int) -> List[StaffAssignment]:
        return self.db.query(StaffAssignment).filter(
            StaffAssignment.assigned_entity == entity_type,
            StaffAssignment.entity_id == entity_id
        ).all()
