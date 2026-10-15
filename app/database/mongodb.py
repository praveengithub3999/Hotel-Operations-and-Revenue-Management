import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://localhost:27017"
)

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=2000)
    db = client["hotel_operations"]
except Exception:
    client = None
    db = None

audit_logs_collection = db["audit_logs"] if db is not None else None
housekeeping_logs_collection = db["housekeeping_logs"] if db is not None else None
maintenance_logs_collection = db["maintenance_logs"] if db is not None else None
guest_feedback_collection = db["guest_feedback"] if db is not None else None
