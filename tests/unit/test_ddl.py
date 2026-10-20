"""Unit tests for DDL and rollback script generation and topological ordering.

Spec: scriptgen/unit-test
"""

import pytest

from schemashift.contracts.schema_map import Column, ForeignKey, Index, SchemaMap, Table
from schemashift.errors import SchemaShiftError
from schemashift.gen.ddl import generate_ddl_sql
from schemashift.gen.rollback import generate_rollback_sql
from schemashift.migrate.ordering import get_table_topological_order


def test_topological_ordering():
    col = Column(name="id", pg_type="CHAR(24)", nullable=False)
    parent = Table(name="orders", columns=[col])
    child = Table(
        name="order_items",
        columns=[col],
        foreign_keys=[ForeignKey(columns=["order_id"], ref_table="orders", ref_columns=["id"])],
    )
    smap = SchemaMap(tables=[child, parent])
    ordered = get_table_topological_order(smap)
    assert [t.name for t in ordered] == ["orders", "order_items"]


def test_cyclic_dependency_raises():
    col = Column(name="id", pg_type="CHAR(24)", nullable=False)
    t1 = Table(
        name="t1",
        columns=[col],
        foreign_keys=[ForeignKey(columns=["t2_id"], ref_table="t2", ref_columns=["id"])],
    )
    t2 = Table(
        name="t2",
        columns=[col],
        foreign_keys=[ForeignKey(columns=["t1_id"], ref_table="t1", ref_columns=["id"])],
    )
    smap = SchemaMap(tables=[t1, t2])
    with pytest.raises(SchemaShiftError) as exc_info:
        get_table_topological_order(smap)
    assert "Circular" in str(exc_info.value)


def test_generate_ddl_and_rollback():
    col1 = Column(name="id", pg_type="CHAR(24)", nullable=False)
    col2 = Column(name="sku", pg_type="TEXT", nullable=False)
    tbl = Table(
        name="products",
        columns=[col1, col2],
        indexes=[Index(columns=["sku"], unique=True)],
    )
    smap = SchemaMap(map_hash="sha256:12345", map_version=1, tables=[tbl])

    ddl = generate_ddl_sql(smap)
    assert 'CREATE TABLE IF NOT EXISTS "products"' in ddl
    assert 'CONSTRAINT "pk_products" PRIMARY KEY ("id")' in ddl
    assert 'CONSTRAINT "uq_products_sku" UNIQUE ("sku")' in ddl

    rollback = generate_rollback_sql(smap)
    assert 'DROP TABLE IF EXISTS "products" CASCADE;' in rollback
