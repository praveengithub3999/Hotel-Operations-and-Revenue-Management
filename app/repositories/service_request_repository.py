from typing import List
from sqlalchemy.orm import Session

from app.models.service_request import ServiceRequest
from app.repositories.base import BaseRepository


class ServiceRequestRepository(BaseRepository[ServiceRequest]):
    def __init__(self, db: Session):
        super().__init__(ServiceRequest, db)

    def get_by_reservation(self, reservation_id: int) -> List[ServiceRequest]:
        return self.db.query(ServiceRequest).filter(
            ServiceRequest.reservation_id == reservation_id
        ).all()

    def get_by_type(self, service_type: str) -> List[ServiceRequest]:
        return self.db.query(ServiceRequest).filter(
            ServiceRequest.service_type == service_type
        ).all()
