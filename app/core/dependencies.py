from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from os import getenv


security = HTTPBearer()

ENVIRONMENT = getenv("ENVIRONMENT", "development")

SECRET_KEY = getenv("SECRET_KEY")

if not SECRET_KEY:
    if ENVIRONMENT.lower() == "production":
        raise RuntimeError(
            "SECRET_KEY must be set in production"
        )

    # Local development only
    SECRET_KEY = "hotel-management-secret-key-2026"

ALGORITHM = getenv("ALGORITHM", "HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")
        username = payload.get("username")
        role = payload.get("role")

        if user_id is None or username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        return {
            "id": int(user_id),
            "username": username,
            "role": role
        }

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )