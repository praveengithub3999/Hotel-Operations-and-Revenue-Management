from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.roles import require_role
from app.database.database import get_db
from app.models.reservation import Reservation
from app.database.mongodb import guest_feedback_collection
from app.utils.audit_logger import create_guest_feedback


class FeedbackCategory(BaseModel):
    room: int = Field(ge=1, le=5, default=5)
    service: int = Field(ge=1, le=5, default=5)
    cleanliness: int = Field(ge=1, le=5, default=5)


class GuestFeedbackCreate(BaseModel):
    reservation_id: int
    rating: int = Field(ge=1, le=5)
    categories: Optional[FeedbackCategory] = None
    comment: str = Field(default="", max_length=1000)


router = APIRouter(
    prefix="/feedback",
    tags=["Guest Feedback"]
)


@router.post(
    "/",
    dependencies=[Depends(require_role("ADMIN", "RECEPTIONIST", "MANAGER"))]
)
def submit_guest_feedback(
    data: GuestFeedbackCreate,
    db: Session = Depends(get_db)
):
    """Store guest stay feedback in MongoDB (PDF Section 18 requirement)."""
    reservation = db.query(Reservation).filter(Reservation.id == data.reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    cat_dict = data.categories.model_dump() if data.categories else {
        "room": data.rating,
        "service": data.rating,
        "cleanliness": data.rating
    }

    feedback_id = create_guest_feedback(
        reservation_id=data.reservation_id,
        rating=data.rating,
        categories=cat_dict,
        comment=data.comment
    )

    return {
        "message": "Guest feedback recorded successfully",
        "feedback_id": feedback_id,
        "reservation_id": data.reservation_id,
        "rating": data.rating
    }


@router.get(
    "/{reservation_id}",
    dependencies=[Depends(require_role("ADMIN", "MANAGER"))]
)
def get_reservation_feedback(reservation_id: int):
    """Retrieve guest feedback from MongoDB."""
    if guest_feedback_collection is None:
        return []
    records = list(guest_feedback_collection.find({"reservation_id": str(reservation_id)}, {"_id": 0}))
    return records
