from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.housekeeping import (
    HousekeepingCreate,
    HousekeepingUpdate,
    HousekeepingResponse
)
from app.services.housekeeping_service import HousekeepingService

router = APIRouter(prefix="/housekeeping", tags=["Housekeeping"])


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
    service = HousekeepingService(db)
    return service.create_task(data, current_user)


@router.get(
    "/",
    response_model=List[HousekeepingResponse],
    dependencies=[Depends(require_role("ADMIN", "HOUSEKEEPING", "MANAGER"))]
)
def get_housekeeping_tasks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "HOUSEKEEPING", "MANAGER")
    )
):
    service = HousekeepingService(db)
    return service.get_tasks(current_user)


# Support POST & GET /housekeeping/tasks (PDF Page 8 alias)
@router.post(
    "/tasks",
    response_model=HousekeepingResponse,
    dependencies=[Depends(require_role("ADMIN", "HOUSEKEEPING"))]
)
def create_housekeeping_task_alias(
    data: HousekeepingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "HOUSEKEEPING")
    )
):
    service = HousekeepingService(db)
    return service.create_task(data, current_user)


@router.get(
    "/tasks",
    response_model=List[HousekeepingResponse],
    dependencies=[Depends(require_role("ADMIN", "HOUSEKEEPING", "MANAGER"))]
)
def get_housekeeping_tasks_alias(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "HOUSEKEEPING", "MANAGER")
    )
):
    service = HousekeepingService(db)
    return service.get_tasks(current_user)


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
    service = HousekeepingService(db)
    return service.get_task_by_id(task_id, current_user)


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
    service = HousekeepingService(db)
    return service.update_task(task_id, data, current_user)


# PUT /rooms/{id}/housekeeping-status (PDF Page 8 API requirement)
# We attach this route directly on room router or housekeeping router
room_hk_router = APIRouter(prefix="/rooms", tags=["Rooms"])


@room_hk_router.put(
    "/{room_id}/housekeeping-status",
    dependencies=[Depends(require_role("ADMIN", "HOUSEKEEPING", "MANAGER"))]
)
def update_room_housekeeping_status(
    room_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """PUT /rooms/{id}/housekeeping-status (PDF Page 8 API requirement)."""
    service = HousekeepingService(db)
    return service.update_room_housekeeping_status(room_id, status)
