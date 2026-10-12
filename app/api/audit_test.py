from fastapi import APIRouter, Depends

from app.utils.audit_logger import create_audit_log
from app.core.roles import require_role


router = APIRouter(
    prefix="/audit",
    tags=["Audit Logs"]
)


@router.post(
    "/test",
    dependencies=[Depends(require_role("ADMIN"))]
)
def create_audit_test_log():
    log_id = create_audit_log(
        action="AUDIT_TEST",
        message="Audit logger is working"
    )

    return {
        "message": "Audit log created successfully",
        "log_id": log_id
    }