"""BSON to PostgreSQL type mapping and transform selection.

Spec: infer/typemap
"""

from __future__ import annotations

from schemashift.contracts.profile import FieldProfile


def select_pg_type_and_transform(field: FieldProfile) -> tuple[str, str, bool]:
    """Given a FieldProfile, return (pg_type, transform_name, is_ambiguous)."""
    types = field.types
    if not types:
        return "TEXT", "null_if_missing", False

    dominant_type = max(types.keys(), key=lambda t: types[t])
    total_samples = sum(types.values())
    purity = types[dominant_type] / total_samples if total_samples else 1.0
    ambiguous = purity < 0.95 or len(types) > 1

    if dominant_type == "objectId":
        return "CHAR(24)", "objectid_hex", ambiguous
    elif dominant_type == "string":
        # Check if mixed with numeric (like rating)
        if len(types) > 1 and any(t in ("int", "double", "decimal") for t in types):
            return "SMALLINT", "int_coerce", True
        return "TEXT", "identity", ambiguous
    elif dominant_type == "int":
        # Check if mixed with string
        if "string" in types:
            return "SMALLINT", "int_coerce", True
        num_range = field.numeric_range
        if num_range and (
            num_range.get("min", 0) < -2147483648 or num_range.get("max", 0) > 2147483647
        ):
            return "BIGINT", "identity", ambiguous
        return "INTEGER", "identity", ambiguous
    elif dominant_type == "double":
        return "DOUBLE PRECISION", "identity", ambiguous
    elif dominant_type == "decimal":
        digits = field.decimal_digits or 2
        p = min(38, max(12, digits + 10))
        return f"NUMERIC({p},{digits})", "decimal_numeric", ambiguous
    elif dominant_type == "bool":
        return "BOOLEAN", "identity", ambiguous
    elif dominant_type == "date":
        return "TIMESTAMPTZ", "date_utc", ambiguous
    elif dominant_type in ("object", "array"):
        return "JSONB", "json_dump", ambiguous
    elif dominant_type == "binData":
        return "BYTEA", "identity", ambiguous
    elif dominant_type == "null":
        return "TEXT", "null_if_missing", False

    return "TEXT", "identity", True
