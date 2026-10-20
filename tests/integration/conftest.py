"""Integration test fixtures and stack readiness verification.

Spec: tests/integration-conftest
"""

import os
import time
import pytest
import psycopg
from pymongo import MongoClient


@pytest.fixture(scope="session")
def mongo_client():
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    for _ in range(10):
        try:
            client.admin.command("ping")
            break
        except Exception:
            time.sleep(1)
    return client


@pytest.fixture(scope="session")
def pg_connection():
    uri = os.environ.get("PG_URI", "postgresql://schemashift:schemashift@localhost:5432/schemashift")
    conn = None
    for _ in range(10):
        try:
            conn = psycopg.connect(uri)
            break
        except Exception:
            time.sleep(1)
    assert conn is not None
    yield conn
    conn.close()
