from fastapi import APIRouter

from app.utils.audit_logger import create_audit_log


router = APIRouter(
    prefix="/audit",
    tags=["Audit Logs"]
)


@router.post("/test")
def create_audit_test_log():
    log_id = create_audit_log(
        action="AUDIT_TEST",
        message="Audit logger is working"
    )

    return {
        "message": "Audit log created successfully",
        "log_id": log_id
    }