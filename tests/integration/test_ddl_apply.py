"""Integration tests for DDL application and rollback against real PostgreSQL.

Spec: tests/integration-ddl
"""

import pytest
from schemashift.contracts.schema_map import Column, ForeignKey, Index, SchemaMap, Table
from schemashift.gen.ddl import generate_ddl_sql
from schemashift.gen.rollback import generate_rollback_sql
from schemashift.migrate.executor import execute_sql_script


@pytest.mark.integration
def test_ddl_apply_and_rollback(pg_connection):
    col = Column(name="id", pg_type="CHAR(24)", nullable=False)
    tbl = Table(
        name="test_integration_items",
        primary_key=["id"],
        columns=[col, Column(name="name", pg_type="TEXT", nullable=True)],
    )
    smap = SchemaMap(tables=[tbl])

    ddl = generate_ddl_sql(smap)
    rollback = generate_rollback_sql(smap)

    # 1. Apply DDL
    conn_str = "postgresql://schemashift:schemashift@localhost:5432/schemashift"
    execute_sql_script(conn_str, ddl)

    # Verify table exists
    with pg_connection.cursor() as cur:
        cur.execute("SELECT count(*) FROM test_integration_items")
        assert cur.fetchone()[0] == 0

    # 2. Apply rollback
    execute_sql_script(conn_str, rollback)

    # Verify table was dropped
    with pg_connection.cursor() as cur:
        cur.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'test_integration_items')"
        )
        assert cur.fetchone()[0] is False
