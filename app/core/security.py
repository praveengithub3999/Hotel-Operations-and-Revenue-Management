from datetime import datetime, timedelta, timezone
from os import getenv

import bcrypt
from jose import jwt


SECRET_KEY = getenv(
    "SECRET_KEY",
    "hotel-management-secret-key-2026"
)

ALGORITHM = getenv(
    "ALGORITHM",
    "HS256"
)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


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