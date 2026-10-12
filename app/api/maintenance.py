from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.roles import require_role
from app.database.database import get_db
from app.models.maintenance import Maintenance
from app.models.housekeeping import Housekeeping
from app.models.reservation import Reservation
from app.models.room import Room
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse
)

router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"]
)


def get_maintenance_or_404(maintenance_id: int, db: Session):
    maintenance = db.query(Maintenance).filter(
        Maintenance.id == maintenance_id
    ).first()

    if not maintenance:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found"
        )

    return maintenance


def check_maintenance_access(maintenance, current_user):
    if (
        current_user["role"] == "MAINTENANCE"
        and maintenance.assigned_to != current_user["username"]
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only access maintenance requests assigned to you"
        )


@router.post(
    "/",
    response_model=MaintenanceResponse
)
def create_maintenance(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "MAINTENANCE")
    )
):
    room = db.query(Room).filter(
        Room.id == data.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    assigned_to = data.assigned_to

    # Maintenance staff can create requests only for themselves.
    if current_user["role"] == "MAINTENANCE":
        assigned_to = current_user["username"]

    maintenance = Maintenance(
        room_id=data.room_id,
        issue=data.issue,
        status="OPEN",
        assigned_to=assigned_to,
        notes=data.notes
    )

    db.add(maintenance)

    # Do not mark an occupied room as available.
    if room.status not in ["OCCUPIED", "OUT_OF_SERVICE"]:
        room.status = "MAINTENANCE"
    else:
        room.status = "OUT_OF_SERVICE"

    db.commit()
    db.refresh(maintenance)

    return maintenance


@router.get(
    "/",
    response_model=list[MaintenanceResponse]
)
def get_maintenance_tasks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "MAINTENANCE", "MANAGER")
    )
):
    query = db.query(Maintenance)

    if current_user["role"] == "MAINTENANCE":
        query = query.filter(
            Maintenance.assigned_to == current_user["username"]
        )

    return query.all()


@router.get(
    "/{maintenance_id}",
    response_model=MaintenanceResponse
)
def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "MAINTENANCE", "MANAGER")
    )
):
    maintenance = get_maintenance_or_404(maintenance_id, db)
    check_maintenance_access(maintenance, current_user)

    return maintenance


@router.put(
    "/{maintenance_id}",
    response_model=MaintenanceResponse
)
def update_maintenance(
    maintenance_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "MAINTENANCE")
    )
):
    maintenance = get_maintenance_or_404(maintenance_id, db)
    check_maintenance_access(maintenance, current_user)

    room = db.query(Room).filter(
        Room.id == maintenance.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    allowed_statuses = [
        "OPEN",
        "ASSIGNED",
        "IN_PROGRESS",
        "ON_HOLD",
        "RESOLVED",
        "CLOSED",
        "CANCELLED"
    ]

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid maintenance status"
        )

    # Only ADMIN can assign or reassign maintenance work.
    if current_user["role"] == "MAINTENANCE":
        if (
            data.assigned_to is not None
            and data.assigned_to != maintenance.assigned_to
        ):
            raise HTTPException(
                status_code=403,
                detail="Only ADMIN can reassign maintenance requests"
            )
    elif data.assigned_to is not None:
        maintenance.assigned_to = data.assigned_to

    maintenance.status = data.status

    if data.notes is not None:
        maintenance.notes = data.notes

    if data.status == "RESOLVED":
        maintenance.resolved_at = datetime.utcnow()

        # Check whether housekeeping still needs to be completed.
        unfinished_task = db.query(Housekeeping).filter(
            Housekeeping.room_id == room.id,
            Housekeeping.status != "CLEAN"
        ).first()

        active_reservation = db.query(Reservation).filter(
            Reservation.room_id == room.id,
            Reservation.status == "CHECKED_IN"
        ).first()

        if active_reservation:
            room.status = "OCCUPIED"
        elif unfinished_task:
            room.status = "DIRTY"
        else:
            room.status = "CLEANING"

    elif data.status in ["OPEN", "ASSIGNED", "IN_PROGRESS", "ON_HOLD"]:
        room.status = "MAINTENANCE"

    elif data.status in ["CLOSED", "CANCELLED"]:
        # Keep the room unavailable until its condition is checked.
        room.status = "CLEANING"

    try:
        db.commit()
        db.refresh(maintenance)
    except Exception:
        db.rollback()
        raise

    return maintenance
