"""Global pytest fixtures and test configuration.

Spec: foundation/conftest
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest

# Ensure source directory is in PYTHONPATH
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
