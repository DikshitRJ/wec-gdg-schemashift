"""Unit tests for migration helpers, failures, and SQL splitting.

Spec: migrate/unit-test
"""

import json
from schemashift.migrate.executor import split_sql_statements
from schemashift.migrate.failures import RowFailure, write_failures_report


def test_split_sql_statements():
    script = """
    -- initial comment
    CREATE TABLE "users" ("id" CHAR(24));
    
    -- another comment
    CREATE TABLE "orders" ("id" CHAR(24));
    """
    stmts = split_sql_statements(script)
    assert len(stmts) == 2
    assert 'CREATE TABLE "users"' in stmts[0]
    assert 'CREATE TABLE "orders"' in stmts[1]


def test_write_failures_report(tmp_path):
    failures = [
        RowFailure(
            collection="reviews",
            doc_id="12345",
            path="rating",
            column="rating",
            value_repr="'great'",
            reason="Cannot coerce string to int",
            hint="Check reviews.rating field",
        )
    ]
    path = write_failures_report(failures, tmp_path)
    with open(path) as f:
        data = json.load(f)
    assert data["total_failures"] == 1
    assert data["failures"][0]["doc_id"] == "12345"
