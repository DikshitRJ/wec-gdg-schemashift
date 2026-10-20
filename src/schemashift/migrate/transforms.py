"""Typed data transformations for data migration.

Spec: migrate/transforms
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable

from bson import Decimal128, ObjectId
from schemashift.errors import SchemaShiftError


class TransformError(SchemaShiftError):
    """Raised when a field value cannot be cleanly transformed."""

    exit_code = 4

    def __init__(self, message: str, *, path: str = "", value_repr: str = "", hint: str = ""):
        hint = hint or f"Value '{value_repr}' at path '{path}' cannot be transformed."
        super().__init__(message, hint=hint)
        self.path = path
        self.value_repr = value_repr


def objectid_hex(val: Any, *, path: str = "") -> str | None:
    """Transform ObjectId to 24-character hexadecimal string."""
    if val is None:
        return None
    if isinstance(val, ObjectId):
        return str(val)
    if isinstance(val, str) and len(val) == 24:
        return val
    try:
        return str(ObjectId(str(val)))
    except Exception as exc:
        raise TransformError(
            f"Cannot convert '{val}' to ObjectId hex: {exc}",
            path=path,
            value_repr=repr(val)[:80],
            hint="Ensure the field contains a 24-hex-character ObjectId string.",
        ) from exc


def date_utc(val: Any, *, path: str = "") -> datetime | None:
    """Transform datetime or ISO string to UTC timezone-aware datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    if isinstance(val, str):
        try:
            # Handle ISO format
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception as exc:
            raise TransformError(
                f"Cannot parse date string '{val}': {exc}",
                path=path,
                value_repr=repr(val)[:80],
                hint="Check date string format. Expected ISO-8601.",
            ) from exc
    raise TransformError(
        f"Unexpected type for date: {type(val)}",
        path=path,
        value_repr=repr(val)[:80],
        hint="Date fields must be datetime objects or ISO-8601 strings.",
    )


def decimal_numeric(val: Any, *, path: str = "") -> Decimal | None:
    """Transform Decimal128, float, int, or numeric str to Decimal."""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    if isinstance(val, Decimal128):
        return val.to_decimal()
    if isinstance(val, (int, float, str)):
        try:
            return Decimal(str(val))
        except Exception as exc:
            raise TransformError(
                f"Cannot convert '{val}' to Decimal: {exc}",
                path=path,
                value_repr=repr(val)[:80],
            ) from exc
    raise TransformError(
        f"Unexpected type for Decimal: {type(val)}",
        path=path,
        value_repr=repr(val)[:80],
    )


def int_coerce(val: Any, *, path: str = "") -> int | None:
    """Coerce int, float, or numeric string to int. Fails on non-numeric strings."""
    if val is None:
        return None
    if isinstance(val, int) and not isinstance(val, bool):
        return val
    if isinstance(val, float):
        return int(val)
    if isinstance(val, str):
        try:
            # Try int conversion
            return int(float(val.strip()))
        except Exception as exc:
            raise TransformError(
                f"Cannot coerce non-numeric string '{val}' to integer",
                path=path,
                value_repr=repr(val)[:80],
                hint="Field has non-numeric values (e.g. 'great'). Review schema or add an override.",
            ) from exc
    raise TransformError(
        f"Unexpected type for integer coercion: {type(val)}",
        path=path,
        value_repr=repr(val)[:80],
    )


def json_dump(val: Any, *, path: str = "") -> str | None:
    """Serialize dict, list, or primitive to JSON string for JSONB storage."""
    if val is None:
        return None

    def _default(o: Any) -> Any:
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, (datetime, Decimal, Decimal128)):
            return str(o)
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    try:
        return json.dumps(val, default=_default, sort_keys=True)
    except Exception as exc:
        raise TransformError(
            f"Failed to serialize value to JSON: {exc}",
            path=path,
            value_repr=repr(val)[:80],
        ) from exc


def null_if_missing(val: Any, *, path: str = "") -> Any:
    """Return None if val is missing or empty."""
    return None if val in ("", None) else val


def identity(val: Any, *, path: str = "") -> Any:
    """Pass-through transform."""
    return val


TRANSFORMS: dict[str, Callable[..., Any]] = {
    "objectid_hex": objectid_hex,
    "date_utc": date_utc,
    "decimal_numeric": decimal_numeric,
    "int_coerce": int_coerce,
    "json_dump": json_dump,
    "null_if_missing": null_if_missing,
    "identity": identity,
}


def apply_transform(name: str, value: Any, *, path: str = "") -> Any:
    """Look up and apply named transform."""
    fn = TRANSFORMS.get(name, identity)
    return fn(value, path=path)
