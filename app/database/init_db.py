
from app.database.database import engine, Base

# Import all models so SQLAlchemy knows about every table
from app.models.user import User
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.models.room import Room
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.service_request import ServiceRequest
from app.models.charge import Charge
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.housekeeping import Housekeeping
from app.models.maintenance import Maintenance
from app.models.refund import Refund

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
