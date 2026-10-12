
from os import getenv

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User


security = HTTPBearer()

ENVIRONMENT = getenv("ENVIRONMENT", "development")
SECRET_KEY = getenv("SECRET_KEY")

if not SECRET_KEY:
    if ENVIRONMENT.lower() == "production":
        raise RuntimeError("SECRET_KEY must be set in production")

    SECRET_KEY = "hotel-management-secret-key-2026"

ALGORITHM = getenv("ALGORITHM", "HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        user = db.query(User).filter(
            User.id == int(user_id)
        ).first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="User not found or inactive"
            )

        return {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }

    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
