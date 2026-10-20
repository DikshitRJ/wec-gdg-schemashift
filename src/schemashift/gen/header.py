"""Header comments for generated migration and ORM scripts.

Spec: scriptgen/header
"""

from __future__ import annotations


def make_sql_header(map_hash: str, map_version: int, generator: str) -> str:
    """Generate SQL header carrying map provenance."""
    return f"-- schemashift map_hash={map_hash} map_version={map_version} generator={generator}\n-- DO NOT EDIT DIRECTLY - GENERATED FROM FROZEN SCHEMA MAP\n\n"


def make_python_header(map_hash: str, map_version: int, generator: str) -> str:
    """Generate Python header carrying map provenance."""
    return f"# schemashift map_hash={map_hash} map_version={map_version} generator={generator}\n# DO NOT EDIT DIRECTLY - GENERATED FROM FROZEN SCHEMA MAP\n\n"
