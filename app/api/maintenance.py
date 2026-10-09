from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.database import get_db
from app.models.maintenance import Maintenance
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


@router.post("/", response_model=MaintenanceResponse)
def create_maintenance(
    data: MaintenanceCreate,
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

    maintenance = Maintenance(
        room_id=data.room_id,
        issue=data.issue,
        status="OPEN",
        assigned_to=data.assigned_to,
        notes=data.notes
    )

    db.add(maintenance)

    # Room is unavailable while under maintenance
    room.status = "MAINTENANCE"

    db.commit()
    db.refresh(maintenance)

    return maintenance


@router.get("/", response_model=list[MaintenanceResponse])
def get_maintenance_tasks(
    db: Session = Depends(get_db)
):
    return db.query(Maintenance).all()


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db)
):
    maintenance = db.query(Maintenance).filter(
        Maintenance.id == maintenance_id
    ).first()

    if not maintenance:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found"
        )

    return maintenance


@router.put("/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance(
    maintenance_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db)
):
    maintenance = db.query(Maintenance).filter(
        Maintenance.id == maintenance_id
    ).first()

    if not maintenance:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found"
        )

    room = db.query(Room).filter(
        Room.id == maintenance.room_id
    ).first()

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

    maintenance.status = data.status

    if data.assigned_to is not None:
        maintenance.assigned_to = data.assigned_to

    if data.notes is not None:
        maintenance.notes = data.notes

    if data.status == "RESOLVED":
        maintenance.resolved_at = datetime.utcnow()
        room.status = "CLEANING"

    elif data.status == "IN_PROGRESS":
        room.status = "MAINTENANCE"

    db.commit()
    db.refresh(maintenance)

    return maintenance