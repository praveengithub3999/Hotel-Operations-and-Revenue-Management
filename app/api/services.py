from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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


@router.post(
    "/",
    response_model=ServiceRequestResponse
)
def create_service_request(
    service: ServiceRequestCreate,
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    return db.query(ServiceRequest).all()


@router.put(
    "/{service_id}",
    response_model=ServiceRequestResponse
)
def update_service_request(
    service_id: int,
    service: ServiceRequestUpdate,
    db: Session = Depends(get_db)
):
    service_request = db.query(ServiceRequest).filter(
        ServiceRequest.id == service_id
    ).first()

    if not service_request:
        raise HTTPException(
            status_code=404,
            detail="Service request not found"
        )

    service_request.status = service.status

    if service.status == "COMPLETED":
        service_request.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(service_request)

    return service_request