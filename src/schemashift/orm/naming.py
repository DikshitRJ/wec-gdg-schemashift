"""Naming conventions for generated ORM classes and attributes.

Spec: orm/naming
"""

from __future__ import annotations

from schemashift.identifiers import singularize, snake_case


def table_to_class_name(table_name: str) -> str:
    """Convert table name (e.g. order_items) to PascalCase class name (OrderItem)."""
    sing = singularize(table_name)
    parts = sing.split("_")
    return "".join(p.capitalize() for p in parts if p)


def column_to_attr_name(column_name: str) -> str:
    """Ensure column name is a valid Python attribute identifier."""
    attr = snake_case(column_name)
    if attr in ("def", "class", "return", "pass", "import", "from", "for", "while"):
        attr = f"{attr}_"
    return attr


def pg_type_to_python_type(pg_type: str) -> tuple[str, str]:
    """Map PostgreSQL column type to (Python type annotation, SQLAlchemy type expression)."""
    p = pg_type.upper().split("(")[0].strip()

    if p in ("CHAR", "VARCHAR", "TEXT"):
        return "str", "Text"
    elif p in ("INTEGER", "SMALLINT"):
        return "int", "Integer"
    elif p == "BIGINT":
        return "int", "BigInteger"
    elif p in ("FLOAT", "DOUBLE PRECISION"):
        return "float", "Float"
    elif p == "NUMERIC":
        return "Decimal", "Numeric"
    elif p == "BOOLEAN":
        return "bool", "Boolean"
    elif p in ("TIMESTAMPTZ", "TIMESTAMP"):
        return "datetime", "DateTime(timezone=True)"
    elif p == "JSONB":
        return "dict[str, Any]", "JSONB"
    elif p == "BYTEA":
        return "bytes", "LargeBinary"

    return "str", "Text"
