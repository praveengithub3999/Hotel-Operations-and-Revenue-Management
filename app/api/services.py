from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.reservation import Reservation
from app.models.service_request import ServiceRequest
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestUpdate,
    ServiceRequestResponse
)

router = APIRouter(
    prefix="/service-requests",
    tags=["Service Requests"]
)

ALLOWED_STATUSES = [
    "REQUESTED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED"
]


@router.post(
    "/",
    response_model=ServiceRequestResponse
)
def create_service_request(
    service: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("ADMIN", "RECEPTIONIST")
    )
):
    reservation = db.query(Reservation).filter(
        Reservation.id == service.reservation_id
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    if reservation.status != "CHECKED_IN":
        raise HTTPException(
            status_code=400,
            detail="Services can only be requested during an active stay"
        )

    if service.quantity < 1:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be at least 1"
        )

    new_service = ServiceRequest(
        reservation_id=reservation.id,
        room_id=reservation.room_id,
        guest_id=reservation.guest_id,
        service_type=service.service_type,
        description=service.description,
        quantity=service.quantity,
        status="REQUESTED"
    )

    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return new_service


@router.get(
    "/",
    response_model=list[ServiceRequestResponse]
)
def get_service_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role(
            "ADMIN",
            "RECEPTIONIST",
            "HOUSEKEEPING",
            "MAINTENANCE",
            "MANAGER"
        )
    )
):
    query = db.query(ServiceRequest)

    # Housekeeping handles housekeeping-related services only.
    if current_user["role"] == "HOUSEKEEPING":
        query = query.filter(
            ServiceRequest.service_type == "HOUSEKEEPING"
        )

    # Maintenance handles maintenance-related services only.
    elif current_user["role"] == "MAINTENANCE":
        query = query.filter(
            ServiceRequest.service_type == "MAINTENANCE"
        )

    return query.all()


@router.put(
    "/{service_id}",
    response_model=ServiceRequestResponse
)
def update_service_request(
    service_id: int,
    service: ServiceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role(
            "ADMIN",
            "RECEPTIONIST",
            "HOUSEKEEPING",
            "MAINTENANCE"
        )
    )
):
    service_request = db.query(ServiceRequest).filter(
        ServiceRequest.id == service_id
    ).first()

    if not service_request:
        raise HTTPException(
            status_code=404,
            detail="Service request not found"
        )

    if service.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid service request status"
        )

    role = current_user["role"]

    # Operational staff can update only their service category.
    if role == "HOUSEKEEPING":
        if service_request.service_type != "HOUSEKEEPING":
            raise HTTPException(
                status_code=403,
                detail="You cannot update this service request"
            )

    elif role == "MAINTENANCE":
        if service_request.service_type != "MAINTENANCE":
            raise HTTPException(
                status_code=403,
                detail="You cannot update this service request"
            )

    # Do not allow completed or cancelled requests to be reopened.
    if service_request.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(
            status_code=400,
            detail="Completed or cancelled requests cannot be changed"
        )

    # Enforce sensible status transitions.
    allowed_transitions = {
        "REQUESTED": ["IN_PROGRESS", "CANCELLED"],
        "IN_PROGRESS": ["COMPLETED", "CANCELLED"]
    }

    if service.status not in allowed_transitions.get(
        service_request.status, []
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid status transition"
        )

    service_request.status = service.status

    if service.status == "COMPLETED":
        service_request.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(service_request)

    return service_request
