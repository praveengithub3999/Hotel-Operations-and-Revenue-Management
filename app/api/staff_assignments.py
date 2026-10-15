from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.staff_assignment import StaffAssignment
from app.models.room import Room
from app.models.maintenance import Maintenance
from app.models.housekeeping import Housekeeping
from app.models.user import User
from app.schemas.staff_assignment import StaffAssignmentCreate, StaffAssignmentResponse
from app.utils.audit_logger import create_audit_log, create_housekeeping_log, create_maintenance_log

router = APIRouter(
    prefix="/staff/assignments",
    tags=["Staff Assignments"]
)


@router.post(
    "/",
    response_model=StaffAssignmentResponse,
    dependencies=[Depends(require_role("ADMIN", "MANAGER"))]
)
def create_staff_assignment(
    data: StaffAssignmentCreate,
    db: Session = Depends(get_db)
):
    """
    POST /staff/assignments (Member 2 API requirement):
    Assign:
    Room -> Housekeeper
    or
    Maintenance Request -> Technician
    """
    # Verify user exists and has appropriate role
    staff_user = db.query(User).filter(User.username == data.staff_username).first()
    if not staff_user:
        raise HTTPException(status_code=404, detail="Staff user not found")

    if data.assigned_entity == "ROOM":
        if staff_user.role not in ["HOUSEKEEPING", "ADMIN"]:
            raise HTTPException(status_code=400, detail="Only housekeeping staff can be assigned to rooms")
        room = db.query(Room).filter(Room.id == data.entity_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Create/update housekeeping task for this assignment
        active_task = db.query(Housekeeping).filter(
            Housekeeping.room_id == room.id,
            Housekeeping.status.notin_(["CLEAN", "CLEANED"])
        ).first()

        if active_task:
            active_task.assigned_to = staff_user.username
            active_task.status = "ASSIGNED"
        else:
            active_task = Housekeeping(
                room_id=room.id,
                status="ASSIGNED",
                assigned_to=staff_user.username,
                notes=data.notes or "Assigned staff member"
            )
            db.add(active_task)

        create_housekeeping_log(
            room=room.room_number,
            staff=staff_user.username,
            action="ASSIGNED_TO_ROOM",
            old_status=room.status,
            new_status="ASSIGNED",
            remarks=data.notes
        )

    elif data.assigned_entity == "MAINTENANCE_REQUEST":
        if staff_user.role not in ["MAINTENANCE", "ADMIN"]:
            raise HTTPException(status_code=400, detail="Only maintenance staff can be assigned to maintenance requests")
        maint = db.query(Maintenance).filter(Maintenance.id == data.entity_id).first()
        if not maint:
            raise HTTPException(status_code=404, detail="Maintenance record not found")

        maint.assigned_to = staff_user.username
        if maint.status == "OPEN":
            maint.status = "ASSIGNED"

        create_maintenance_log(
            room_id=maint.room_id,
            maintenance_id=maint.id,
            staff=staff_user.username,
            action="ASSIGNED_TO_TECHNICIAN",
            status=maint.status,
            details={"notes": data.notes}
        )

    assignment = StaffAssignment(
        staff_username=data.staff_username,
        staff_role=data.staff_role,
        assigned_entity=data.assigned_entity,
        entity_id=data.entity_id,
        notes=data.notes
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    create_audit_log(
        action="STAFF_ASSIGNMENT",
        message=f"Assigned {data.staff_username} to {data.assigned_entity} {data.entity_id}",
        entity="staff_assignment",
        entity_id=assignment.id
    )

    return assignment


@router.get(
    "/",
    response_model=List[StaffAssignmentResponse],
    dependencies=[Depends(require_role("ADMIN", "MANAGER", "HOUSEKEEPING", "MAINTENANCE"))]
)
def get_staff_assignments(
    staff_username: str | None = None,
    db: Session = Depends(get_db)
):
    """GET /staff/assignments (Member 2 API requirement)."""
    query = db.query(StaffAssignment)
    if staff_username:
        query = query.filter(StaffAssignment.staff_username == staff_username)
    return query.order_by(StaffAssignment.id.desc()).all()
