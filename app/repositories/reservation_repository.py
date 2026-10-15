from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.repositories.base import BaseRepository

ACTIVE_STATUSES = ["PENDING", "CONFIRMED", "CHECKED_IN"]


class ReservationRepository(BaseRepository[Reservation]):
    def __init__(self, db: Session):
        super().__init__(Reservation, db)

    def find_overlapping(
        self,
        room_id: int,
        check_in_date: date,
        check_out_date: date,
        exclude_id: Optional[int] = None,
        for_update: bool = False
    ) -> Optional[Reservation]:
        query = self.db.query(Reservation).filter(
            Reservation.room_id == room_id,
            Reservation.status.in_(ACTIVE_STATUSES),
            Reservation.check_in_date < check_out_date,
            Reservation.check_out_date > check_in_date
        )
        if exclude_id is not None:
            query = query.filter(Reservation.id != exclude_id)
        if for_update:
            query = query.with_for_update()
        return query.first()

    def get_by_guest(self, guest_id: int) -> List[Reservation]:
        return self.db.query(Reservation).filter(Reservation.guest_id == guest_id).all()

    def get_by_room(self, room_id: int) -> List[Reservation]:
        return self.db.query(Reservation).filter(Reservation.room_id == room_id).all()

    def get_confirmed_past_checkin(self, cutoff_date: date) -> List[Reservation]:
        return self.db.query(Reservation).filter(
            Reservation.status == "CONFIRMED",
            Reservation.check_in_date < cutoff_date
        ).all()
