"""Name and type normalization used by similarity scoring.

Spec: similarity/normalize
"""

from __future__ import annotations

from schemashift.identifiers import singularize, snake_case

_STOP_TOKENS = {"id", "mongo", "bson", "field", "col", "column"}


def normalize_name(name: str) -> str:
    """Normalize a field or column name into comparable token representation."""
    # Handle dot paths (take leaf)
    leaf = name.split(".")[-1].replace("[]", "")
    s = snake_case(leaf)
    tokens = [t for t in s.split("_") if t and t not in _STOP_TOKENS]
    if not tokens:
        tokens = [s]
    # Singularize tokens
    norm_tokens = [singularize(t) for t in tokens]
    return " ".join(norm_tokens)


_TYPE_FAMILY_MAP = {
    # Ints
    "int": "int",
    "int32": "int",
    "int64": "int",
    "integer": "int",
    "bigint": "int",
    "smallint": "int",
    # Floats / Decimals
    "double": "float",
    "float": "float",
    "double precision": "float",
    "decimal": "decimal",
    "decimal128": "decimal",
    "numeric": "decimal",
    # Strings
    "string": "text",
    "text": "text",
    "varchar": "text",
    "char": "text",
    # Booleans
    "bool": "bool",
    "boolean": "bool",
    # Dates
    "date": "timestamp",
    "datetime": "timestamp",
    "timestamptz": "timestamp",
    "timestamp": "timestamp",
    # Objects / Arrays
    "object": "json",
    "dict": "json",
    "array": "array",
    "list": "array",
    "jsonb": "json",
    # Binary
    "bindata": "bytes",
    "bytes": "bytes",
    "bytea": "bytes",
    # ObjectIds / Refs
    "objectid": "ref",
    "char(24)": "ref",
    "null": "null",
}


def normalize_type(type_name: str) -> str:
    """Normalize a BSON or SQL type string to a canonical family."""
    raw = type_name.lower().split("(")[0].strip()
    return _TYPE_FAMILY_MAP.get(raw, raw)
