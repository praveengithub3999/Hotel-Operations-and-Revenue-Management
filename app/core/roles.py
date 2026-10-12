
from fastapi import Depends, HTTPException
from app.core.dependencies import get_current_user


ROLE_PERMISSIONS = {
    "ADMIN": [
        "hotel_management",
        "staff_management",
        "room_management",
        "tax_configuration",
        "all_reports",
    ],
    "RECEPTIONIST": [
        "guest_management",
        "reservation_management",
        "availability",
        "checkin_checkout",
        "guest_services",
    ],
    "HOUSEKEEPING": [
        "assigned_rooms",
        "cleaning_status",
        "room_problems",
        "mark_room_clean",
    ],
    "MAINTENANCE": [
        "maintenance_requests",
        "maintenance_assignments",
        "repair_status",
        "maintenance_notes",
    ],
    "FINANCE": [
        "invoices",
        "payments",
        "refunds",
        "revenue_reports",
    ],
    "MANAGER": [
        "occupancy_reports",
        "revenue_reports",
        "room_performance",
        "staff_workload",
        "operational_reports",
    ],
}


def require_role(*required_roles: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in required_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource",
            )
        return current_user

    return role_checker
