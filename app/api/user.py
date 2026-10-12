
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import StaffCreate, UserResponse
from app.core.security import hash_password
from app.core.roles import require_role


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


ALLOWED_ROLES = [
    "ADMIN",
    "RECEPTIONIST",
    "HOUSEKEEPING",
    "MAINTENANCE",
    "FINANCE",
    "MANAGER"
]


@router.post(
    "/register",
    response_model=UserResponse,
    dependencies=[Depends(require_role("ADMIN"))]
)
def register_user(
    user: StaffCreate,
    db: Session = Depends(get_db)
):
    try:
        username = user.username.strip()
        email = user.email.strip().lower()
        role = user.role.strip().upper()

        if role not in ALLOWED_ROLES:
            raise HTTPException(
                status_code=400,
                detail="Invalid role. Choose one of the six approved roles."
            )

        # Check username and email without case sensitivity
        existing_user = db.query(User).filter(
            (func.lower(User.username) == username.lower()) |
            (func.lower(User.email) == email)
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Username or email already exists"
            )

        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(user.password),
            role=role
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
