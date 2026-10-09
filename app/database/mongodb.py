from pymongo import MongoClient


MONGO_URL = "mongodb://localhost:27017"

client = MongoClient(MONGO_URL)

mongo_db = client["hotel_operations"]

audit_logs_collection = mongo_db["audit_logs"]