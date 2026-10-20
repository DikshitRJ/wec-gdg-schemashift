"""Declarative ETL plan generation and documentation.

Spec: scriptgen/etl-plan
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemashift.contracts.schema_map import SchemaMap
from schemashift.migrate.ordering import get_table_topological_order


def generate_etl_plan(schema_map: SchemaMap) -> dict[str, Any]:
    """Generate declarative ETL plan from a frozen SchemaMap."""
    tables = get_table_topological_order(schema_map)

    tables_plan: list[dict[str, Any]] = []

    for tbl in tables:
        col_plans: list[dict[str, Any]] = []
        for col in tbl.columns:
            col_plans.append(
                {
                    "name": col.name,
                    "pg_type": col.pg_type,
                    "source_path": col.source_path,
                    "transform": col.transform,
                    "on_error": col.on_error,
                    "nullable": col.nullable,
                    "identity": col.identity,
                }
            )

        tbl_plan: dict[str, Any] = {
            "name": tbl.name,
            "kind": tbl.kind,
            "source_collection": tbl.origin_collection,
            "iteration_path": tbl.origin_path,
            "primary_key": tbl.primary_key,
            "columns": col_plans,
            "foreign_keys": [fk.model_dump() for fk in tbl.foreign_keys],
        }

        if tbl.kind == "child":
            # Identify parent FK column
            parent_fk = next((fk for fk in tbl.foreign_keys if fk.on_delete == "CASCADE"), None)
            if parent_fk:
                tbl_plan["parent_fk_col"] = parent_fk.columns[0]
                tbl_plan["parent_ref_table"] = parent_fk.ref_table

        tables_plan.append(tbl_plan)

    return {
        "map_hash": schema_map.map_hash,
        "map_version": schema_map.map_version,
        "source_database": schema_map.source.database,
        "tables": tables_plan,
    }


def write_etl_artifacts(schema_map: SchemaMap, out_dir: str | Path) -> tuple[str, str]:
    """Write etl_plan.json and etl_pipeline.md to etl/."""
    etl_dir = Path(out_dir) / "etl"
    etl_dir.mkdir(parents=True, exist_ok=True)

    plan = generate_etl_plan(schema_map)
    json_path = etl_dir / "etl_plan.json"
    json_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Generate markdown documentation
    md_lines: list[str] = [
        "# ETL Migration Pipeline Plan",
        "",
        f"**Source Database:** `{schema_map.source.database}`",
        f"**Schema Map Hash:** `{schema_map.map_hash}` (v{schema_map.map_version})",
        "",
        "## Execution Order (Topological)",
        "",
    ]

    for idx, t in enumerate(plan["tables"], start=1):
        md_lines.append(f"### {idx}. Table `{t['name']}` ({t['kind']})")
        md_lines.append(f"- **Source Collection:** `{t['source_collection']}`")
        if t["iteration_path"]:
            md_lines.append(f"- **Array Expansion Path:** `{t['iteration_path']}`")
        md_lines.append("")
        md_lines.append("| Column | PostgreSQL Type | Source Path | Transform | Nullable |")
        md_lines.append("|---|---|---|---|---|")
        for c in t["columns"]:
            md_lines.append(
                f"| `{c['name']}` | `{c['pg_type']}` | `{c['source_path'] or '-'}` | `{c['transform']}` | {c['nullable']} |"
            )
        md_lines.append("")

    doc_path = etl_dir / "etl_pipeline.md"
    doc_path.write_text("\n".join(md_lines), encoding="utf-8")

    return str(json_path.resolve()), str(doc_path.resolve())
