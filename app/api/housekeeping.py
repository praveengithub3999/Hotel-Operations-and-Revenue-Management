from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.roles import require_role
from app.database.database import get_db
from app.models.housekeeping import Housekeeping
from app.models.room import Room
from app.models.reservation import Reservation
from app.schemas.housekeeping import (
    HousekeepingCreate,
    HousekeepingUpdate,
    HousekeepingResponse
)

router = APIRouter(prefix="/housekeeping", tags=["Housekeeping"])


def get_task_or_404(task_id: int, db: Session):
    task = db.query(Housekeeping).filter(
        Housekeeping.id == task_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Housekeeping task not found")

    return task


def check_task_access(task, current_user):
    if (
        current_user["role"] == "HOUSEKEEPING"
        and task.assigned_to != current_user["username"]
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only access tasks assigned to you"
        )


def update_room_status(room, task, db):
    if task.status == "CLEANING_IN_PROGRESS":
        room.status = "CLEANING"

    elif task.status == "CLEAN":
        task.completed_at = datetime.utcnow()

        # Do not make a room available if another housekeeping
        # task is still unfinished.
        other_tasks = db.query(Housekeeping).filter(
            Housekeeping.room_id == room.id,
            Housekeeping.id != task.id,
            Housekeeping.status != "CLEAN"
        ).first()

        if other_tasks:
            room.status = "DIRTY"
            return

        # Do not make a room available while a guest is checked in.
        active_reservation = db.query(Reservation).filter(
            Reservation.room_id == room.id,
            Reservation.status == "CHECKED_IN"
        ).first()

        if active_reservation:
            room.status = "OCCUPIED"
            return

        # Keep rooms unavailable if they are under maintenance.
        if room.status in ["MAINTENANCE", "OUT_OF_SERVICE"]:
            return

        room.status = "AVAILABLE"

    else:
        room.status = "DIRTY"


@router.post(
    "/",
    response_model=HousekeepingResponse,
    dependencies=[Depends(require_role("ADMIN", "HOUSEKEEPING"))]
)
def create_housekeeping_task(
    data: HousekeepingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "HOUSEKEEPING")
    )
):
    room = db.query(Room).filter(Room.id == data.room_id).first()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    assigned_to = data.assigned_to

    # Housekeeping staff can create tasks only for themselves.
    if current_user["role"] == "HOUSEKEEPING":
        assigned_to = current_user["username"]

    task = Housekeeping(
        room_id=data.room_id,
        status="DIRTY",
        assigned_to=assigned_to,
        notes=data.notes
    )

    db.add(task)
    room.status = "DIRTY"
    db.commit()
    db.refresh(task)

    return task


@router.get(
    "/",
    response_model=list[HousekeepingResponse],
    dependencies=[Depends(require_role("ADMIN", "HOUSEKEEPING", "MANAGER"))]
)
def get_housekeeping_tasks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "HOUSEKEEPING", "MANAGER")
    )
):
    query = db.query(Housekeeping)

    if current_user["role"] == "HOUSEKEEPING":
        query = query.filter(
            Housekeeping.assigned_to == current_user["username"]
        )

    return query.all()


@router.get(
    "/{task_id}",
    response_model=HousekeepingResponse,
    dependencies=[Depends(require_role("ADMIN", "HOUSEKEEPING", "MANAGER"))]
)
def get_housekeeping_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "HOUSEKEEPING", "MANAGER")
    )
):
    task = get_task_or_404(task_id, db)
    check_task_access(task, current_user)
    return task


@router.put(
    "/{task_id}",
    response_model=HousekeepingResponse,
    dependencies=[Depends(require_role("ADMIN", "HOUSEKEEPING"))]
)
def update_housekeeping_task(
    task_id: int,
    data: HousekeepingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "HOUSEKEEPING")
    )
):
    task = get_task_or_404(task_id, db)
    check_task_access(task, current_user)

    room = db.query(Room).filter(Room.id == task.room_id).first()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    allowed_statuses = [
        "DIRTY",
        "CLEANING_IN_PROGRESS",
        "INSPECTED",
        "CLEAN"
    ]

    if data.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid housekeeping status")

    # Only an ADMIN can reassign a task.
    if current_user["role"] == "HOUSEKEEPING":
        if data.assigned_to is not None and data.assigned_to != task.assigned_to:
            raise HTTPException(
                status_code=403,
                detail="Only an ADMIN can reassign housekeeping tasks"
            )
    elif data.assigned_to is not None:
        task.assigned_to = data.assigned_to

    task.status = data.status

    if data.notes is not None:
        task.notes = data.notes

    update_room_status(room, task, db)

    db.commit()
    db.refresh(task)

    return task
