# schemashift map_hash=sha256:a6dfb0cbaaa0ab1359eb734eda0c7299de6dff4cc78daf6700c410ab03f866e6 map_version=1 generator=orm_generator
# DO NOT EDIT DIRECTLY - GENERATED FROM FROZEN SCHEMA MAP


"""Database connection and session factory.

Spec: orm/db
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

PG_URI = os.environ.get("PG_URI", "postgresql://schemashift:schemashift@localhost:5432/schemashift")
# Use psycopg 3 engine URL
if PG_URI.startswith("postgresql://") and "+psycopg" not in PG_URI:
    ENGINE_URI = PG_URI.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    ENGINE_URI = PG_URI

engine = create_engine(ENGINE_URI, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
