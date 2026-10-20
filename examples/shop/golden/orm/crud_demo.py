# schemashift map_hash=sha256:a6dfb0cbaaa0ab1359eb734eda0c7299de6dff4cc78daf6700c410ab03f866e6 map_version=1 generator=orm_generator
# DO NOT EDIT DIRECTLY - GENERATED FROM FROZEN SCHEMA MAP


"""Executable smoke script demonstrating CRUD operations with generated ORM.

Spec: orm/crud-demo
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

try:
    from orm.db import SessionLocal
    from orm.repositories import UserRepository
except ImportError:
    try:
        from .db import SessionLocal
        from .repositories import UserRepository
    except (ImportError, ValueError):
        from db import SessionLocal
        from repositories import UserRepository

def main():
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        # Test list
        users = repo.list(limit=5)
        print(f"Listed {len(users)} users from PostgreSQL.")
        # Test create
        new_id = str(ObjectId())
        user = repo.create(
            id=new_id,
            email=f"smoke.{new_id[:6]}@example.com",
            name="Smoke Test",
            address_street="123 Test St",
            address_city="Springfield",
            address_state="IL",
            address_zip="62701",
            address_geo_lat=40.0,
            address_geo_lng=-89.0,
            prefs_newsletter=False,
            prefs_theme="dark",
            created_at=datetime.now(timezone.utc),
        )
        print(f"Created user: {user.id}")
        # Test get
        fetched = repo.get(new_id)
        assert fetched is not None
        print(f"Retrieved user: {fetched.name}")
        # Test delete
        deleted = repo.delete(new_id)
        assert deleted
        print("Deleted smoke user successfully.")
        print("CRUD smoke test passed!")
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())
