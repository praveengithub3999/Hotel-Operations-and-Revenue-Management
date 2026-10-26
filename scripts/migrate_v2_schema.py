"""
Database migration script to add missing columns and create new tables
for both dev and test databases without data loss.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

def migrate_database(db_url: str, label: str):
    print(f"--- Migrating {label} Database ---")
    if not db_url:
        print("URL is empty, skipping.")
        return

    # Normalize url driver if needed
    if db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    engine = create_engine(db_url)
    insp = inspect(engine)
    existing_tables = insp.get_table_names()

    with engine.begin() as conn:
        # 1. Update guests table
        if "guests" in existing_tables:
            guest_cols = [c["name"] for c in insp.get_columns("guests")]
            if "emergency_contact" not in guest_cols:
                print("Adding emergency_contact to guests...")
                conn.execute(text("ALTER TABLE guests ADD COLUMN emergency_contact VARCHAR(50);"))

        # 2. Update housekeeping table
        if "housekeeping" in existing_tables:
            hk_cols = [c["name"] for c in insp.get_columns("housekeeping")]
            if "task_type" not in hk_cols:
                print("Adding task_type to housekeeping...")
                conn.execute(text("ALTER TABLE housekeeping ADD COLUMN task_type VARCHAR(50) DEFAULT 'CLEANING';"))
            if "priority" not in hk_cols:
                print("Adding priority to housekeeping...")
                conn.execute(text("ALTER TABLE housekeeping ADD COLUMN priority VARCHAR(20) DEFAULT 'MEDIUM';"))
            if "started_at" not in hk_cols:
                print("Adding started_at to housekeeping...")
                conn.execute(text("ALTER TABLE housekeeping ADD COLUMN started_at TIMESTAMP;"))
            if "remarks" not in hk_cols:
                print("Adding remarks to housekeeping...")
                conn.execute(text("ALTER TABLE housekeeping ADD COLUMN remarks VARCHAR(255);"))

        # 3. Update maintenance table
        if "maintenance" in existing_tables:
            maint_cols = [c["name"] for c in insp.get_columns("maintenance")]
            if "reported_by" not in maint_cols:
                print("Adding reported_by to maintenance...")
                conn.execute(text("ALTER TABLE maintenance ADD COLUMN reported_by VARCHAR(100);"))
            if "category" not in maint_cols:
                print("Adding category to maintenance...")
                conn.execute(text("ALTER TABLE maintenance ADD COLUMN category VARCHAR(50) DEFAULT 'GENERAL';"))
            if "priority" not in maint_cols:
                print("Adding priority to maintenance...")
                conn.execute(text("ALTER TABLE maintenance ADD COLUMN priority VARCHAR(20) DEFAULT 'MEDIUM';"))
            if "description" not in maint_cols:
                print("Adding description to maintenance...")
                conn.execute(text("ALTER TABLE maintenance ADD COLUMN description VARCHAR(255);"))

    # 4. Create new tables via Base.metadata.create_all
    from app.database.database import Base
    from app.models.discount import Discount
    from app.models.staff_assignment import StaffAssignment
    Base.metadata.create_all(bind=engine)
    print(f"Migration completed for {label}!\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        custom_url = sys.argv[1].strip()
        print(f"Running migration on provided database URL: {custom_url[:25]}...")
        migrate_database(custom_url, "REMOTE / NEON")
    else:
        # Migrate test database
        load_dotenv(".env.test", override=True)
        test_url = os.getenv("TEST_DATABASE_URL")
        if test_url:
            migrate_database(test_url, "TEST")

        # Migrate dev database
        load_dotenv(".env", override=True)
        dev_url = os.getenv("DATABASE_URL")
        if dev_url:
            migrate_database(dev_url, "DEVELOPMENT")
