from datetime import datetime, timedelta, timezone
from os import getenv

import bcrypt
from jose import jwt


ENVIRONMENT = getenv("ENVIRONMENT", "development")

SECRET_KEY = getenv("SECRET_KEY")

if not SECRET_KEY:
    if ENVIRONMENT.lower() == "production":
        raise RuntimeError(
            "SECRET_KEY must be set in production"
        )

    SECRET_KEY = "hotel-management-secret-key-2026"

ALGORITHM = getenv("ALGORITHM", "HS256")


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError(
            "Password must not exceed 72 bytes when encoded as UTF-8"
        )

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    password_bytes = plain_password.encode("utf-8")

    if len(password_bytes) > 72:
        return False

    try:
        return bcrypt.checkpw(
            password_bytes,
            hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    data: dict,
    expires_minutes: int = 60
):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )