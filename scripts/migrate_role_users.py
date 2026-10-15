import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.database.database import engine as source_engine
from app.models.user import User


APPROVED_USERS = {
    "receptionist2",
    "housekeeping1",
    "maintenance1",
    "finance1",
    "manager1",
}


def main():
    production_url = os.getenv("PRODUCTION_DATABASE_URL")

    if not production_url:
        raise RuntimeError("PRODUCTION_DATABASE_URL is not set.")

    source_url = source_engine.url
    destination_url = make_url(production_url)

    # Safety checks: never copy from the test database.
    if source_url.database != "hotel_management" or source_url.host not in (
        "localhost",
        "127.0.0.1",
    ):
        raise RuntimeError(
            "Source must be local hotel_management, not a test or remote database."
        )

    if (
        destination_url.database != "neondb"
        or not destination_url.host
        or not destination_url.host.endswith(".neon.tech")
    ):
        raise RuntimeError("Destination is not the expected Neon neondb database.")

    source_factory = sessionmaker(bind=source_engine)
    destination_engine = create_engine(production_url)
    destination_factory = sessionmaker(bind=destination_engine)

    source_db = source_factory()
    destination_db = destination_factory()

    try:
        source_users = (
            source_db.query(User)
            .filter(User.username.in_(APPROVED_USERS))
            .order_by(User.username)
            .all()
        )

        found = {user.username for user in source_users}
        missing_source = APPROVED_USERS - found

        if missing_source:
            raise RuntimeError(
                f"Approved source accounts missing: {sorted(missing_source)}"
            )

        conflicts = []
        for user in source_users:
            username_match = (
                destination_db.query(User)
                .filter(User.username == user.username)
                .first()
            )
            email_match = (
                destination_db.query(User)
                .filter(User.email == user.email)
                .first()
            )

            if username_match or email_match:
                conflicts.append({
                    "username": user.username,
                    "username_conflict": bool(username_match),
                    "email_conflict": bool(email_match),
                })

        print("Source: local hotel_management")
        print("Destination: Neon neondb")
        print("\nApproved accounts:")
        for user in source_users:
            print(f"- {user.username}: {user.role}, active={user.is_active}")

        if conflicts:
            print("\nSTOPPED: production username/email conflicts found:")
            for conflict in conflicts:
                print(conflict)
            print("No records were copied. Resolve conflicts before proceeding.")
            return

        print("\nDry run successful: all five accounts can be copied.")
        print("Existing production accounts will not be overwritten.")
        print("Password hashes will be preserved; new IDs will be assigned.")

        if "--apply" not in sys.argv:
            print("\nDry run only. No database changes were made.")
            print("After reviewing this output, use --apply to perform the migration.")
            return
        destination_db.rollback()

        # Recheck and insert within one transaction.
        with destination_db.begin():
            for user in source_users:
                username_exists = (
                    destination_db.query(User.id)
                    .filter(User.username == user.username)
                    .first()
                )
                email_exists = (
                    destination_db.query(User.id)
                    .filter(User.email == user.email)
                    .first()
                )

                if username_exists or email_exists:
                    raise RuntimeError(
                        f"Conflict appeared for {user.username}; migration cancelled."
                    )

                destination_db.add(User(
                    username=user.username,
                    email=user.email,
                    password_hash=user.password_hash,
                    role=user.role,
                    is_active=user.is_active,
                ))

        print("\nMigration completed. Five approved accounts were copied.")

    finally:
        source_db.close()
        destination_db.close()
        destination_engine.dispose()


if __name__ == "__main__":
    main()

