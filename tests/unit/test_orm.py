"""Unit tests for ORM generator and naming helpers.

Spec: orm/unit-test
"""

from schemashift.contracts.schema_map import Column, SchemaMap, Table
from schemashift.orm.generator import generate_orm_package
from schemashift.orm.naming import column_to_attr_name, pg_type_to_python_type, table_to_class_name


def test_orm_naming():
    assert table_to_class_name("users") == "User"
    assert table_to_class_name("order_items") == "OrderItem"
    assert column_to_attr_name("class") == "class_"
    assert column_to_attr_name("email") == "email"

    py_type, sa_type = pg_type_to_python_type("CHAR(24)")
    assert py_type == "str"
    assert "Text" in sa_type


def test_generate_orm_package(tmp_path):
    col = Column(name="id", pg_type="CHAR(24)", nullable=False)
    tbl = Table(name="users", kind="root", primary_key=["id"], columns=[col])
    smap = SchemaMap(tables=[tbl])

    res = generate_orm_package(smap, tmp_path)
    assert "models" in res
    assert "repositories" in res
    assert "db" in res

    # Check files exist
    orm_dir = tmp_path / "orm"
    assert (orm_dir / "models.py").exists()
    assert (orm_dir / "repositories.py").exists()
    assert (orm_dir / "app.env").exists()
    assert (orm_dir / "REFACTOR_NOTES.md").exists()
