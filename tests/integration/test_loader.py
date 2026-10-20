"""Integration tests for DataLoader against real MongoDB and PostgreSQL.

Spec: tests/integration-loader
"""

import pytest

from schemashift.contracts.schema_map import Column, SchemaMap, Table
from schemashift.gen.ddl import generate_ddl_sql
from schemashift.migrate.executor import execute_sql_script
from schemashift.migrate.loader import DataLoader
from schemashift.seed.shop import seed_shop


@pytest.mark.integration
def test_loader_end_to_end(mongo_client, pg_connection):
    # Seed mongo
    seed_shop(mongo_client)

    # Prepare simple schema map for users
    col_id = Column(name="id", pg_type="CHAR(24)", source_path="_id", transform="objectid_hex")
    col_email = Column(name="email", pg_type="TEXT", source_path="email", transform="identity")
    tbl = Table(
        name="users", origin_collection="users", primary_key=["id"], columns=[col_id, col_email]
    )
    smap = SchemaMap(
        source={"kind": "mongodb", "database": "shop", "collections": ["users"]}, tables=[tbl]
    )

    # Drop existing table if any to ensure clean test schema
    with pg_connection.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")

    # Apply DDL
    pg_uri = "postgresql://schemashift:schemashift@localhost:5432/schemashift"
    ddl = generate_ddl_sql(smap)
    execute_sql_script(pg_uri, ddl)

    # Run loader
    loader = DataLoader(
        mongo_uri="mongodb://localhost:27017",
        pg_uri=pg_uri,
        schema_map=smap,
        truncate=True,
    )
    res = loader.load_all()
    assert res.get("users", 0) == 200

    # Verify rows in PostgreSQL
    with pg_connection.cursor() as cur:
        cur.execute("SELECT count(*) FROM users")
        cnt = cur.fetchone()[0]
        assert cnt == 200
