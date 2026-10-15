from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.models.room import Room
from app.models.reservation import Reservation
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.refund import Refund
from app.repositories.guest_repository import GuestRepository
from app.repositories.hotel_repository import RoomRepository
from app.repositories.reservation_repository import ReservationRepository, ACTIVE_STATUSES
from app.schemas.reservation import ReservationCreate, ReservationUpdate
from app.utils.audit_logger import create_audit_log

UNAVAILABLE_ROOM_STATUSES = [
    "DIRTY",
    "CLEANING",
    "MAINTENANCE",
    "OUT_OF_SERVICE",
    "OCCUPIED"
]


class ReservationService:
    def __init__(self, db: Session):
        self.db = db
        self.reservation_repo = ReservationRepository(db)
        self.guest_repo = GuestRepository(db)
        self.room_repo = RoomRepository(db)

    def create_reservation(self, data: ReservationCreate) -> Reservation:
        guest = self.guest_repo.get_by_id(data.guest_id)
        if not guest:
            raise HTTPException(status_code=404, detail="Guest not found")

        # Concurrency safety: lock room row
        room = self.room_repo.get_by_id(data.room_id, for_update=True)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.status in UNAVAILABLE_ROOM_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Room is not currently ready for reservation"
            )

        overlapping = self.reservation_repo.find_overlapping(
            room_id=data.room_id,
            check_in_date=data.check_in_date,
            check_out_date=data.check_out_date,
            for_update=True
        )
        if overlapping:
            raise HTTPException(
                status_code=400,
                detail="Room is already reserved for these dates"
            )

        reservation = Reservation(
            guest_id=data.guest_id,
            room_id=data.room_id,
            check_in_date=data.check_in_date,
            check_out_date=data.check_out_date,
            number_of_guests=data.number_of_guests,
            status="CONFIRMED",
            special_requests=data.special_requests
        )
        saved = self.reservation_repo.create(reservation)

        create_audit_log(
            action="CREATE_RESERVATION",
            message=f"Reservation created for guest {guest.id} in room {room.id}",
            reservation_id=saved.id,
            entity="reservation",
            entity_id=saved.id,
            details={"room_number": room.room_number, "guests": data.number_of_guests}
        )
        return saved

    def get_reservations(self) -> List[Reservation]:
        return self.reservation_repo.get_all()

    def get_reservation_by_id(self, reservation_id: int) -> Reservation:
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return reservation

    def update_reservation(self, reservation_id: int, data: ReservationUpdate) -> Reservation:
        """Modify reservation (dates, room, guests, special requests)."""
        reservation = self.reservation_repo.get_by_id(reservation_id, for_update=True)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if reservation.status not in ["PENDING", "CONFIRMED"]:
            raise HTTPException(
                status_code=400,
                detail="Only pending or confirmed reservations can be modified"
            )

        target_room_id = data.room_id if data.room_id is not None else reservation.room_id
        target_check_in = data.check_in_date if data.check_in_date is not None else reservation.check_in_date
        target_check_out = data.check_out_date if data.check_out_date is not None else reservation.check_out_date

        if target_check_in >= target_check_out:
            raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")

        # Check overlapping for target room and dates
        overlapping = self.reservation_repo.find_overlapping(
            room_id=target_room_id,
            check_in_date=target_check_in,
            check_out_date=target_check_out,
            exclude_id=reservation.id,
            for_update=True
        )
        if overlapping:
            raise HTTPException(
                status_code=400,
                detail="Room is already reserved for these dates"
            )

        if data.room_id is not None:
            room = self.room_repo.get_by_id(data.room_id)
            if not room:
                raise HTTPException(status_code=404, detail="Room not found")
            reservation.room_id = data.room_id

        if data.check_in_date is not None:
            reservation.check_in_date = data.check_in_date
        if data.check_out_date is not None:
            reservation.check_out_date = data.check_out_date
        if data.number_of_guests is not None:
            reservation.number_of_guests = data.number_of_guests
        if data.special_requests is not None:
            reservation.special_requests = data.special_requests
        if data.status is not None:
            reservation.status = data.status

        saved = self.reservation_repo.update(reservation)
        create_audit_log(
            action="MODIFY_RESERVATION",
            message=f"Reservation {saved.id} modified",
            reservation_id=saved.id,
            entity="reservation",
            entity_id=saved.id
        )
        return saved

    def cancel_reservation(self, reservation_id: int) -> Dict[str, Any]:
        """Cancel reservation with cancellation policy refund tiers (Section 28 Feature 4)."""
        reservation = self.reservation_repo.get_by_id(reservation_id, for_update=True)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if reservation.status not in ["PENDING", "CONFIRMED"]:
            raise HTTPException(
                status_code=400,
                detail="Only pending or confirmed reservations can be cancelled"
            )

        # Cancellation Policy Calculation:
        # > 7 days before check-in: 100% refund
        # 3 - 7 days: 50% partial refund
        # < 3 days: 0% refund (cancellation fee applies)
        today = date.today()
        days_until_checkin = (reservation.check_in_date - today).days

        if days_until_checkin > 7:
            refund_tier = "FULL_REFUND"
            refund_percentage = Decimal("1.00")
        elif 3 <= days_until_checkin <= 7:
            refund_tier = "PARTIAL_REFUND_50"
            refund_percentage = Decimal("0.50")
        else:
            refund_tier = "CANCELLATION_FEE_APPLIED"
            refund_percentage = Decimal("0.00")

        reservation.status = "CANCELLED"
        self.db.commit()

        create_audit_log(
            action="CANCEL_RESERVATION",
            message=f"Reservation {reservation.id} cancelled. Policy tier: {refund_tier}",
            reservation_id=reservation.id,
            entity="reservation",
            entity_id=reservation.id,
            details={"days_until_checkin": days_until_checkin, "refund_tier": refund_tier}
        )

        return {
            "message": "Reservation cancelled successfully",
            "reservation_id": reservation.id,
            "status": reservation.status,
            "cancellation_policy": {
                "days_until_checkin": days_until_checkin,
                "refund_tier": refund_tier,
                "eligible_refund_percentage": float(refund_percentage * 100)
            }
        }

    def process_no_shows(self) -> List[Dict[str, Any]]:
        """
        No-Show Management (Section 28 Feature 5):
        If guest doesn't arrive by check-in date cutoff:
        CONFIRMED -> NO_SHOW
        """
        today = date.today()
        confirmed_past = self.reservation_repo.get_confirmed_past_checkin(today)
        processed = []

        for res in confirmed_past:
            res.status = "NO_SHOW"
            processed.append({
                "reservation_id": res.id,
                "room_id": res.room_id,
                "check_in_date": str(res.check_in_date),
                "status": "NO_SHOW"
            })
            create_audit_log(
                action="NO_SHOW",
                message=f"Reservation {res.id} marked as NO_SHOW (check-in was {res.check_in_date})",
                reservation_id=res.id,
                entity="reservation",
                entity_id=res.id
            )

        if processed:
            self.db.commit()

        return processed
