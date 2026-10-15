from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.database.mongodb import (
    audit_logs_collection,
    housekeeping_logs_collection,
    maintenance_logs_collection,
    guest_feedback_collection,
)


def create_audit_log(
    action: str,
    message: str = "",
    user_id: Any = None,
    reservation_id: Any = None,
    entity: str = "reservation",
    entity_id: Any = None,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Record an audit event adhering to PDF Section 18."""
    if audit_logs_collection is None:
        return None

    now = datetime.now(timezone.utc)
    log = {
        "user_id": str(user_id) if user_id is not None else None,
        "action": action,
        "message": message,
        "entity": entity,
        "entity_id": str(entity_id or reservation_id) if (entity_id or reservation_id) else None,
        "reservation_id": reservation_id,
        "timestamp": now.isoformat(),
        "created_at": now,
        "details": details or ({"message": message} if message else {}),
    }

    try:
        result = audit_logs_collection.insert_one(log)
        return str(result.inserted_id)
    except Exception:
        return None


def create_housekeeping_log(
    room: Any,
    staff: Optional[str],
    action: str,
    old_status: str,
    new_status: str,
    remarks: Optional[str] = None,
) -> Optional[str]:
    """Track housekeeping event adhering to PDF Section 18."""
    if housekeeping_logs_collection is None:
        return None

    now = datetime.now(timezone.utc)
    log = {
        "room": str(room),
        "staff": staff,
        "action": action,
        "old_status": old_status,
        "new_status": new_status,
        "timestamp": now.isoformat(),
        "created_at": now,
        "remarks": remarks or "",
    }

    try:
        result = housekeeping_logs_collection.insert_one(log)
        return str(result.inserted_id)
    except Exception:
        return None


def create_maintenance_log(
    room_id: Any,
    maintenance_id: Any,
    staff: Optional[str],
    action: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Track maintenance event adhering to PDF Section 18."""
    if maintenance_logs_collection is None:
        return None

    now = datetime.now(timezone.utc)
    log = {
        "room_id": str(room_id),
        "maintenance_id": str(maintenance_id),
        "staff": staff,
        "action": action,
        "status": status,
        "timestamp": now.isoformat(),
        "created_at": now,
        "details": details or {},
    }

    try:
        result = maintenance_logs_collection.insert_one(log)
        return str(result.inserted_id)
    except Exception:
        return None


def create_guest_feedback(
    reservation_id: Any,
    rating: int,
    categories: Optional[Dict[str, int]] = None,
    comment: str = "",
) -> Optional[str]:
    """Record guest stay feedback adhering to PDF Section 18."""
    if guest_feedback_collection is None:
        return None

    now = datetime.now(timezone.utc)
    log = {
        "reservation_id": str(reservation_id),
        "rating": rating,
        "categories": categories or {"room": rating, "service": rating, "cleanliness": rating},
        "comment": comment,
        "timestamp": now.isoformat(),
        "created_at": now,
    }

    try:
        result = guest_feedback_collection.insert_one(log)
        return str(result.inserted_id)
    except Exception:
        return None