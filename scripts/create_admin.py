
import os
import sys
import getpass

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.exc import IntegrityError

from app.database.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password


def main():
    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password: ")

    if not username or not email or len(password) < 12:
        print("Enter a username, email, and password of at least 12 characters.")
        return

    db = SessionLocal()

    try:
        existing = db.query(User).filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing:
            print("That username or email already exists. No changes made.")
            return

        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="ADMIN",
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("Admin account created successfully.")

    except IntegrityError:
        db.rollback()
        print("Username or email already exists. No changes made.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
