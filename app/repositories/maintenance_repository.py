from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.maintenance import Maintenance
from app.repositories.base import BaseRepository


class MaintenanceRepository(BaseRepository[Maintenance]):
    def __init__(self, db: Session):
        super().__init__(Maintenance, db)

    def get_by_room(self, room_id: int) -> List[Maintenance]:
        return self.db.query(Maintenance).filter(Maintenance.room_id == room_id).all()

    def get_by_assigned(self, username: str) -> List[Maintenance]:
        return self.db.query(Maintenance).filter(Maintenance.assigned_to == username).all()

    def get_active_for_room(self, room_id: int, exclude_id: Optional[int] = None) -> Optional[Maintenance]:
        query = self.db.query(Maintenance).filter(
            Maintenance.room_id == room_id,
            Maintenance.status.notin_(["RESOLVED", "CLOSED", "CANCELLED"])
        )
        if exclude_id is not None:
            query = query.filter(Maintenance.id != exclude_id)
        return query.first()
