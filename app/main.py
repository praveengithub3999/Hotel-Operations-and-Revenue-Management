from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.hotels import router as hotel_router
from app.api.room_type import router as room_type_router
from app.api.rooms import router as room_router
from app.api.guests import router as guest_router
from app.api.reservations import router as reservation_router
from app.api.services import router as service_router
from app.api.charges import router as charge_router
from app.api.invoices import router as invoice_router
from app.api.payments import router as payment_router
from app.api.refund import router as refund_router
from app.api.checkout import router as checkout_router
from app.api.housekeeping import router as housekeeping_router
from app.api.maintenance import router as maintenance_router
from app.api.mongo_test import router as mongo_test_router
from app.api.audit_test import router as audit_test_router
from app.api.user import router as users_router
from app.api.auth import router as auth_router
from app.api.reports import router as reports_router

app = FastAPI(
    title="StayEase Hotel Operations & Revenue Management System",
    description="Backend system for hotel operations and revenue management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hotel_router)
app.include_router(room_type_router)
app.include_router(room_router)
app.include_router(guest_router)
app.include_router(reservation_router)
app.include_router(service_router)
app.include_router(charge_router)
app.include_router(invoice_router)
app.include_router(payment_router)
app.include_router(refund_router)
app.include_router(checkout_router)
app.include_router(housekeeping_router)
app.include_router(maintenance_router)
app.include_router(mongo_test_router)
app.include_router(audit_test_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(reports_router)

@app.get("/")
def home():
    return {
        "message": "StayEase Hotel Management System is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }