"""Parse and apply user-provided schema overrides.

Spec: freeze-gate/overrides
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from schemashift.contracts.schema_map import Column, SchemaMap, Table
from schemashift.errors import ConfigurationError


def load_overrides(file_path: str | Path) -> list[dict[str, Any]]:
    """Load overrides from YAML file."""
    p = Path(file_path)
    if not p.exists():
        return []
    try:
        content = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return content.get("overrides", [])
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to parse overrides file '{p}': {exc}",
            hint="Check YAML syntax in the overrides file.",
        ) from exc


def apply_overrides(schema_map: SchemaMap, overrides: list[dict[str, Any]]) -> SchemaMap:
    """Apply overrides to a SchemaMap, mutating or returning updated copy."""
    if not overrides:
        return schema_map

    for item in overrides:
        target = item.get("target", "")
        settings = item.get("set", {})
        if not target or not settings:
            continue

        parts = target.split(".")
        if len(parts) == 1:
            # Table-level override (e.g. rename table)
            target_table = parts[0]
            for tbl in schema_map.tables:
                if tbl.name == target_table:
                    if "rename" in settings:
                        tbl.name = settings["rename"]
        elif len(parts) == 2:
            # Column-level override (e.g. reviews.rating)
            target_table, target_col = parts[0], parts[1]
            for tbl in schema_map.tables:
                # Match by table name or collection name
                if tbl.name == target_table or tbl.origin_collection == target_table:
                    for col in tbl.columns:
                        if col.name == target_col or col.source_path.split(".")[-1] == target_col:
                            if "pg_type" in settings:
                                col.pg_type = settings["pg_type"]
                            if "transform" in settings:
                                col.transform = settings["transform"]
                            if "on_error" in settings:
                                col.on_error = settings["on_error"]
                            if "nullable" in settings:
                                col.nullable = bool(settings["nullable"])

    return schema_map
