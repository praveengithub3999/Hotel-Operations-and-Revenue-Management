from fastapi import APIRouter, Depends

from app.database.mongodb import audit_logs_collection
from app.core.roles import require_role


router = APIRouter(
    prefix="/mongo",
    tags=["MongoDB"]
)


@router.get(
    "/test",
    dependencies=[Depends(require_role("ADMIN"))]
)
def check_mongodb():
    result = audit_logs_collection.insert_one({
        "action": "API_TEST",
        "message": "MongoDB connection from FastAPI is working"
    })

    return {
        "message": "MongoDB connection successful",
        "inserted_id": str(result.inserted_id)
    }
