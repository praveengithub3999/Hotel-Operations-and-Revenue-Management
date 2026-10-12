
import os
from dotenv import load_dotenv

# Load test database settings first
os.environ["TESTING"] = "1"
load_dotenv(".env.test", override=True)

from app.database.database import Base, engine

# Import all models so SQLAlchemy registers their tables
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.models.room import Room
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.charge import Charge
from app.models.user import User
from app.models.housekeeping import Housekeeping
from app.models.maintenance import Maintenance

# Create tables that don't exist yet
Base.metadata.create_all(bind=engine)

print("Test database tables created successfully.")
