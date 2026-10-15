from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.housekeeping import Housekeeping
from app.repositories.base import BaseRepository


class HousekeepingRepository(BaseRepository[Housekeeping]):
    def __init__(self, db: Session):
        super().__init__(Housekeeping, db)

    def get_by_room(self, room_id: int) -> List[Housekeeping]:
        return self.db.query(Housekeeping).filter(Housekeeping.room_id == room_id).all()

    def get_by_assigned(self, username: str) -> List[Housekeeping]:
        return self.db.query(Housekeeping).filter(Housekeeping.assigned_to == username).all()

    def get_unfinished_for_room(self, room_id: int, exclude_id: Optional[int] = None) -> Optional[Housekeeping]:
        query = self.db.query(Housekeeping).filter(
            Housekeeping.room_id == room_id,
            Housekeeping.status.notin_(["CLEAN", "CLEANED"])
        )
        if exclude_id is not None:
            query = query.filter(Housekeeping.id != exclude_id)
        return query.first()
