from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.maintenance import Maintenance
from app.models.room import Room
from app.models.housekeeping import Housekeeping
from app.models.reservation import Reservation
from app.repositories.hotel_repository import RoomRepository
from app.repositories.maintenance_repository import MaintenanceRepository
from app.repositories.housekeeping_repository import HousekeepingRepository
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.utils.audit_logger import create_maintenance_log

ALLOWED_MAINTENANCE_STATUSES = [
    "OPEN",
    "ASSIGNED",
    "IN_PROGRESS",
    "ON_HOLD",
    "RESOLVED",
    "CLOSED",
    "CANCELLED"
]

SLA_HOURS = {
    "CRITICAL": 2,
    "HIGH": 6,
    "MEDIUM": 24,
    "LOW": 48
}


class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db
        self.maintenance_repo = MaintenanceRepository(db)
        self.room_repo = RoomRepository(db)
        self.housekeeping_repo = HousekeepingRepository(db)

    def create_request(self, data: MaintenanceCreate, current_user: Dict[str, Any]) -> Maintenance:
        room = self.room_repo.get_by_id(data.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        assigned_to = data.assigned_to
        if current_user.get("role") == "MAINTENANCE":
            assigned_to = current_user.get("username")

        issue_text = data.issue or data.description or "General Maintenance"
        priority_val = (data.priority or "MEDIUM").upper()
        if priority_val not in SLA_HOURS:
            priority_val = "MEDIUM"

        maintenance = Maintenance(
            room_id=data.room_id,
            issue=issue_text,
            description=data.description or issue_text,
            category=data.category or "GENERAL",
            priority=priority_val,
            reported_by=data.reported_by or current_user.get("username"),
            status="OPEN",
            assigned_to=assigned_to,
            notes=data.notes
        )
        self.db.add(maintenance)

        if room.status not in ["OCCUPIED", "OUT_OF_SERVICE"]:
            room.status = "MAINTENANCE"
        else:
            room.status = "OUT_OF_SERVICE"

        self.db.commit()
        self.db.refresh(maintenance)

        create_maintenance_log(
            room_id=room.id,
            maintenance_id=maintenance.id,
            staff=assigned_to,
            action="CREATE_MAINTENANCE",
            status="OPEN",
            details={
                "issue": issue_text,
                "priority": priority_val,
                "sla_hours": SLA_HOURS[priority_val]
            }
        )
        return maintenance

    def get_requests(self, current_user: Dict[str, Any]) -> List[Maintenance]:
        if current_user.get("role") == "MAINTENANCE":
            return self.maintenance_repo.get_by_assigned(current_user["username"])
        return self.maintenance_repo.get_all()

    def get_request_by_id(self, maintenance_id: int, current_user: Dict[str, Any]) -> Maintenance:
        record = self.maintenance_repo.get_by_id(maintenance_id)
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")

        if current_user.get("role") == "MAINTENANCE" and record.assigned_to != current_user.get("username"):
            raise HTTPException(status_code=403, detail="You can only access maintenance requests assigned to you")
        return record

    def update_request(
        self,
        maintenance_id: int,
        data: MaintenanceUpdate,
        current_user: Dict[str, Any]
    ) -> Maintenance:
        record = self.get_request_by_id(maintenance_id, current_user)
        room = self.room_repo.get_by_id(record.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        new_status = data.status.upper()
        if new_status not in ALLOWED_MAINTENANCE_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid maintenance status")

        if current_user.get("role") == "MAINTENANCE":
            if data.assigned_to is not None and data.assigned_to != record.assigned_to:
                raise HTTPException(status_code=403, detail="Only ADMIN can reassign maintenance requests")
        elif data.assigned_to is not None:
            record.assigned_to = data.assigned_to

        record.status = new_status
        if data.notes is not None:
            record.notes = data.notes
        if data.description is not None:
            record.description = data.description
        if data.category is not None:
            record.category = data.category
        if data.priority is not None:
            record.priority = data.priority.upper()

        if new_status == "RESOLVED":
            record.resolved_at = datetime.utcnow()
            unfinished_hk = self.housekeeping_repo.get_unfinished_for_room(room.id)
            active_res = self.db.query(Reservation).filter(
                Reservation.room_id == room.id,
                Reservation.status == "CHECKED_IN"
            ).first()

            if active_res:
                room.status = "OCCUPIED"
            elif unfinished_hk:
                room.status = "DIRTY"
            else:
                room.status = "CLEANING"
        elif new_status in ["OPEN", "ASSIGNED", "IN_PROGRESS", "ON_HOLD"]:
            room.status = "MAINTENANCE"
        elif new_status in ["CLOSED", "CANCELLED"]:
            room.status = "CLEANING"

        self.db.commit()
        self.db.refresh(record)

        create_maintenance_log(
            room_id=room.id,
            maintenance_id=record.id,
            staff=record.assigned_to,
            action=f"UPDATE_STATUS_{new_status}",
            status=new_status,
            details={"notes": data.notes}
        )
        return record

    def check_sla_status(self, maintenance_id: int) -> Dict[str, Any]:
        """Check SLA breach status based on priority (Section 28 Feature 7)."""
        record = self.maintenance_repo.get_by_id(maintenance_id)
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")

        priority = (record.priority or "MEDIUM").upper()
        allowed_hours = SLA_HOURS.get(priority, 24)
        deadline = record.created_at + timedelta(hours=allowed_hours)

        now = record.resolved_at or datetime.utcnow()
        is_breached = now > deadline

        return {
            "maintenance_id": record.id,
            "priority": priority,
            "sla_target_hours": allowed_hours,
            "created_at": record.created_at.isoformat(),
            "deadline": deadline.isoformat(),
            "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
            "is_breached": is_breached,
            "status": record.status
        }
