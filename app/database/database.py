
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Find the project root regardless of the terminal's current directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load the correct environment file.
if os.getenv("TESTING") == "1":
    env_file = PROJECT_ROOT / ".env.test"
    load_dotenv(env_file, override=True)
else:
    env_file = PROJECT_ROOT / ".env"
    load_dotenv(env_file)

TESTING = os.getenv("TESTING") == "1"

if TESTING:
    DATABASE_URL = os.getenv("TEST_DATABASE_URL")

    if not DATABASE_URL:
        raise RuntimeError(
            "TEST_DATABASE_URL is missing from the project root .env.test"
        )
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
