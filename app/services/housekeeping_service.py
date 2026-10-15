from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.housekeeping import Housekeeping
from app.models.room import Room
from app.models.reservation import Reservation
from app.repositories.hotel_repository import RoomRepository
from app.repositories.housekeeping_repository import HousekeepingRepository
from app.schemas.housekeeping import HousekeepingCreate, HousekeepingUpdate
from app.utils.audit_logger import create_housekeeping_log

VALID_HOUSEKEEPING_STATUSES = [
    "DIRTY",
    "TASK_CREATED",
    "ASSIGNED",
    "CLEANING_IN_PROGRESS",
    "CLEANED",
    "CLEAN",
    "INSPECTED",
    "FAILED"
]


class HousekeepingService:
    def __init__(self, db: Session):
        self.db = db
        self.housekeeping_repo = HousekeepingRepository(db)
        self.room_repo = RoomRepository(db)

    def create_task(self, data: HousekeepingCreate, current_user: Dict[str, Any]) -> Housekeeping:
        room = self.room_repo.get_by_id(data.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        assigned_to = data.assigned_to
        if current_user.get("role") == "HOUSEKEEPING":
            assigned_to = current_user.get("username")

        task = Housekeeping(
            room_id=data.room_id,
            status="DIRTY",
            task_type=data.task_type or "CLEANING",
            priority=data.priority or "MEDIUM",
            assigned_to=assigned_to,
            notes=data.notes,
            remarks=data.remarks
        )
        self.db.add(task)
        room.status = "DIRTY"
        self.db.commit()
        self.db.refresh(task)

        create_housekeeping_log(
            room=room.room_number,
            staff=assigned_to,
            action="CREATE_TASK",
            old_status=room.status,
            new_status="DIRTY",
            remarks=data.notes or "New cleaning task created"
        )
        return task

    def get_tasks(self, current_user: Dict[str, Any]) -> List[Housekeeping]:
        if current_user.get("role") == "HOUSEKEEPING":
            return self.housekeeping_repo.get_by_assigned(current_user["username"])
        return self.housekeeping_repo.get_all()

    def get_task_by_id(self, task_id: int, current_user: Dict[str, Any]) -> Housekeeping:
        task = self.housekeeping_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Housekeeping task not found")

        if current_user.get("role") == "HOUSEKEEPING" and task.assigned_to != current_user.get("username"):
            raise HTTPException(status_code=403, detail="You can only access tasks assigned to you")
        return task

    def update_task(
        self,
        task_id: int,
        data: HousekeepingUpdate,
        current_user: Dict[str, Any]
    ) -> Housekeeping:
        task = self.get_task_by_id(task_id, current_user)
        room = self.room_repo.get_by_id(task.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        old_status = task.status
        new_status = data.status.upper()

        if new_status not in VALID_HOUSEKEEPING_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid housekeeping status")

        # Housekeeper cannot reassign task to someone else
        if current_user.get("role") == "HOUSEKEEPING":
            if data.assigned_to is not None and data.assigned_to != task.assigned_to:
                raise HTTPException(status_code=403, detail="Only an ADMIN can reassign housekeeping tasks")
        elif data.assigned_to is not None:
            task.assigned_to = data.assigned_to

        task.status = new_status
        if data.notes is not None:
            task.notes = data.notes
        if data.remarks is not None:
            task.remarks = data.remarks
        if data.task_type is not None:
            task.task_type = data.task_type
        if data.priority is not None:
            task.priority = data.priority

        # Room status sync logic
        if new_status == "CLEANING_IN_PROGRESS":
            room.status = "CLEANING"
            if not task.started_at:
                task.started_at = datetime.utcnow()
        elif new_status in ["CLEAN", "CLEANED"]:
            task.completed_at = datetime.utcnow()
            other_unfinished = self.housekeeping_repo.get_unfinished_for_room(room.id, exclude_id=task.id)
            if other_unfinished:
                room.status = "DIRTY"
            else:
                active_res = self.db.query(Reservation).filter(
                    Reservation.room_id == room.id,
                    Reservation.status == "CHECKED_IN"
                ).first()
                if active_res:
                    room.status = "OCCUPIED"
                elif room.status in ["MAINTENANCE", "OUT_OF_SERVICE"]:
                    pass
                else:
                    room.status = "AVAILABLE"
        elif new_status == "FAILED":
            room.status = "DIRTY"
        else:
            if new_status in ["DIRTY", "TASK_CREATED", "ASSIGNED"]:
                room.status = "DIRTY"

        self.db.commit()
        self.db.refresh(task)

        create_housekeeping_log(
            room=room.room_number,
            staff=task.assigned_to,
            action=f"UPDATE_STATUS_{new_status}",
            old_status=old_status,
            new_status=new_status,
            remarks=data.remarks or data.notes
        )
        return task

    def update_room_housekeeping_status(self, room_id: int, status: str) -> Dict[str, Any]:
        """PUT /rooms/{id}/housekeeping-status (Member 2 API requirement)."""
        room = self.room_repo.get_by_id(room_id, for_update=True)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        status_norm = status.upper().strip()
        allowed = ["CLEAN", "DIRTY", "CLEANING_IN_PROGRESS", "INSPECTED", "OUT_OF_SERVICE"]
        if status_norm not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid housekeeping status. Allowed: {allowed}")

        old_room_status = room.status
        if status_norm in ["CLEAN", "INSPECTED"]:
            room.status = "AVAILABLE"
        elif status_norm == "CLEANING_IN_PROGRESS":
            room.status = "CLEANING"
        elif status_norm == "DIRTY":
            room.status = "DIRTY"
        elif status_norm == "OUT_OF_SERVICE":
            room.status = "OUT_OF_SERVICE"

        self.db.commit()
        self.db.refresh(room)

        create_housekeeping_log(
            room=room.room_number,
            staff=None,
            action="ROOM_STATUS_CHANGE",
            old_status=old_room_status,
            new_status=room.status,
            remarks=f"Direct room housekeeping status changed to {status_norm}"
        )

        return {
            "room_id": room.id,
            "room_number": room.room_number,
            "housekeeping_status": status_norm,
            "room_status": room.status
        }
