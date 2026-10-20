"""Unit tests for ETL plan and data transforms.

Spec: scriptgen/etl-unit-test
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from bson import Decimal128, ObjectId

from schemashift.contracts.schema_map import Column, SchemaMap, Table
from schemashift.gen.etl_plan import generate_etl_plan
from schemashift.migrate.transforms import (
    TransformError,
    date_utc,
    decimal_numeric,
    int_coerce,
    json_dump,
    objectid_hex,
)


def test_transforms():
    # ObjectId
    oid = ObjectId("507f1f77bcf86cd799439011")
    assert objectid_hex(oid) == "507f1f77bcf86cd799439011"
    assert objectid_hex(None) is None

    # Date
    dt = datetime(2024, 1, 15, 12, 0, 0)
    res_dt = date_utc(dt)
    assert res_dt is not None
    assert res_dt.tzinfo == UTC

    iso_dt = date_utc("2024-01-15T12:00:00Z")
    assert iso_dt is not None

    with pytest.raises(TransformError):
        date_utc("not-a-date")

    # Decimal
    assert decimal_numeric(Decimal128("19.99")) == Decimal("19.99")
    assert decimal_numeric(19.99) == Decimal("19.99")

    # Int coerce
    assert int_coerce(5) == 5
    assert int_coerce("5") == 5
    assert int_coerce("  42  ") == 42
    with pytest.raises(TransformError):
        int_coerce("great")

    # JSON dump
    data = {"key": "val", "num": 1}
    assert json_dump(data) == '{"key": "val", "num": 1}'


def test_generate_etl_plan():
    col = Column(name="id", pg_type="CHAR(24)", source_path="_id", transform="objectid_hex")
    tbl = Table(name="users", origin_collection="users", columns=[col])
    smap = SchemaMap(tables=[tbl])

    plan = generate_etl_plan(smap)
    assert len(plan["tables"]) == 1
    assert plan["tables"][0]["name"] == "users"
    assert plan["tables"][0]["columns"][0]["transform"] == "objectid_hex"
