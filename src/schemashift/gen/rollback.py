"""PostgreSQL rollback script generator.

Spec: scriptgen/rollback
"""

from __future__ import annotations

from pathlib import Path

from schemashift.contracts.schema_map import SchemaMap
from schemashift.gen.header import make_sql_header
from schemashift.identifiers import quote_ident
from schemashift.migrate.ordering import get_table_topological_order


def generate_rollback_sql(schema_map: SchemaMap) -> str:
    """Render rollback script dropping tables in reverse topological order."""
    tables = get_table_topological_order(schema_map)
    # Reverse order so child tables are dropped before parent tables
    rev_tables = list(reversed(tables))

    lines: list[str] = [make_sql_header(schema_map.map_hash, schema_map.map_version, "rollback")]

    for tbl in rev_tables:
        tbl_q = quote_ident(tbl.name)
        lines.append(f"DROP TABLE IF EXISTS {tbl_q} CASCADE;")

    lines.append("")
    return "\n".join(lines)


def write_rollback(schema_map: SchemaMap, out_path: str | Path) -> str:
    """Generate and write rollback SQL file."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    sql = generate_rollback_sql(schema_map)
    p.write_text(sql, encoding="utf-8")
    return str(p.resolve())
