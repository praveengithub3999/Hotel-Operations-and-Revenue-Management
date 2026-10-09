from datetime import datetime

from app.database.mongodb import audit_logs_collection


def create_audit_log(
    action: str,
    message: str,
    user_id: int = None,
    reservation_id: int = None
):
    log = {
        "action": action,
        "message": message,
        "user_id": user_id,
        "reservation_id": reservation_id,
        "created_at": datetime.utcnow()
    }

    result = audit_logs_collection.insert_one(log)

    return str(result.inserted_id)