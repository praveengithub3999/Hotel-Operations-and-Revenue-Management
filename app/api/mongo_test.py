from fastapi import APIRouter

from app.database.mongodb import audit_logs_collection


router = APIRouter(
    prefix="/mongo",
    tags=["MongoDB"]
)


@router.get("/test")
def check_mongodb():
    result = audit_logs_collection.insert_one({
        "action": "API_TEST",
        "message": "MongoDB connection from FastAPI is working"
    })

    return {
        "message": "MongoDB connection successful",
        "inserted_id": str(result.inserted_id)
    }