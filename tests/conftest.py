"""Global pytest fixtures and test configuration.

Spec: foundation/conftest
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest
from pymongo import MongoClient

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "shop"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to fixtures/shop/ directory."""
    return FIXTURES_DIR


@pytest.fixture
def mongo_uri() -> str:
    """MongoDB connection URI from environment or default."""
    return os.environ.get("MONGO_URI", "mongodb://localhost:27017")


@pytest.fixture
def pg_uri() -> str:
    """PostgreSQL connection URI from environment or default."""
    return os.environ.get(
        "PG_URI", "postgresql://schemashift:schemashift@localhost:5432/schemashift"
    )


@pytest.fixture
def mongo_client(mongo_uri: str) -> MongoClient:  # type: ignore[type-arg]
    """Connected MongoClient fixture."""
    return MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)


@pytest.fixture
def pg_connection(pg_uri: str) -> psycopg.Connection:  # type: ignore[type-arg]
    """Connected psycopg connection fixture with autocommit."""
    conn = psycopg.connect(pg_uri, autocommit=True)
    yield conn
    conn.close()
