from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse
)
from app.services.maintenance_service import MaintenanceService

router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"]
)

maintenance_requests_router = APIRouter(
    prefix="/maintenance-requests",
    tags=["Maintenance Requests"]
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
    service = MaintenanceService(db)
    return service.create_request(data, current_user)


@router.get(
    "/",
    response_model=List[MaintenanceResponse]
)
def get_maintenance_tasks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "MAINTENANCE", "MANAGER")
    )
):
    service = MaintenanceService(db)
    return service.get_requests(current_user)


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
    service = MaintenanceService(db)
    return service.get_request_by_id(maintenance_id, current_user)


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
    service = MaintenanceService(db)
    return service.update_request(maintenance_id, data, current_user)


@router.get(
    "/{maintenance_id}/sla"
)
def get_maintenance_sla(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "MAINTENANCE", "MANAGER")
    )
):
    """Check Maintenance SLA breach and target hours (Section 28 Feature 7)."""
    service = MaintenanceService(db)
    return service.check_sla_status(maintenance_id)


# Endpoints for PDF Page 8: /maintenance-requests
@maintenance_requests_router.post(
    "/",
    response_model=MaintenanceResponse
)
def create_maintenance_request(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN", "MAINTENANCE"))
):
    service = MaintenanceService(db)
    return service.create_request(data, current_user)


@maintenance_requests_router.get(
    "/",
    response_model=List[MaintenanceResponse]
)
def get_maintenance_requests_list(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN", "MAINTENANCE", "MANAGER"))
):
    service = MaintenanceService(db)
    return service.get_requests(current_user)


@maintenance_requests_router.get(
    "/{id}",
    response_model=MaintenanceResponse
)
def get_maintenance_request(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN", "MAINTENANCE", "MANAGER"))
):
    service = MaintenanceService(db)
    return service.get_request_by_id(id, current_user)


@maintenance_requests_router.put(
    "/{id}",
    response_model=MaintenanceResponse
)
def update_maintenance_request(
    id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN", "MAINTENANCE"))
):
    service = MaintenanceService(db)
    return service.update_request(id, data, current_user)
