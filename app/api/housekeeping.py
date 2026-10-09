from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.database import get_db
from app.models.housekeeping import Housekeeping
from app.models.room import Room
from app.schemas.housekeeping import (
    HousekeepingCreate,
    HousekeepingUpdate,
    HousekeepingResponse
)


router = APIRouter(
    prefix="/housekeeping",
    tags=["Housekeeping"]
)


@router.post("/", response_model=HousekeepingResponse)
def create_housekeeping_task(
    data: HousekeepingCreate,
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(
        Room.id == data.room_id
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    task = Housekeeping(
        room_id=data.room_id,
        status="DIRTY",
        assigned_to=data.assigned_to,
        notes=data.notes
    )

    db.add(task)

    # Room must be dirty before cleaning
    room.status = "DIRTY"

    db.commit()
    db.refresh(task)

    return task


@router.get("/", response_model=list[HousekeepingResponse])
def get_housekeeping_tasks(
    db: Session = Depends(get_db)
):
    return db.query(Housekeeping).all()


@router.get("/{task_id}", response_model=HousekeepingResponse)
def get_housekeeping_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(Housekeeping).filter(
        Housekeeping.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Housekeeping task not found"
        )

    return task


@router.put("/{task_id}", response_model=HousekeepingResponse)
def update_housekeeping_task(
    task_id: int,
    data: HousekeepingUpdate,
    db: Session = Depends(get_db)
):
    task = db.query(Housekeeping).filter(
        Housekeeping.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Housekeeping task not found"
        )

    room = db.query(Room).filter(
        Room.id == task.room_id
    ).first()

    allowed_statuses = [
        "DIRTY",
        "CLEANING_IN_PROGRESS",
        "INSPECTED",
        "CLEAN"
    ]

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid housekeeping status"
        )

    task.status = data.status

    if data.assigned_to is not None:
        task.assigned_to = data.assigned_to

    if data.notes is not None:
        task.notes = data.notes

    # Room state changes
    if data.status == "CLEANING_IN_PROGRESS":
        room.status = "CLEANING"

    elif data.status == "CLEAN":
        room.status = "AVAILABLE"
        task.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    return task