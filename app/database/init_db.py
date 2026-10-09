from app.database.database import engine, Base

from app.models.user import User
from app.models.hotel import Hotel
from app.models.room_type import RoomType
from app.models.room import Room


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()