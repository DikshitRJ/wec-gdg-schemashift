"""Foreign key orphan detection across migrated tables.

Spec: verify/orphans
"""

from __future__ import annotations

import psycopg
from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.verify import CheckResult
from schemashift.identifiers import quote_ident


def verify_orphans(
    pg_conn_str: str,
    schema_map: SchemaMap,
) -> list[CheckResult]:
    """Check for orphaned foreign key references in target database."""
    results: list[CheckResult] = []

    with psycopg.connect(pg_conn_str) as conn:
        with conn.cursor() as cur:
            for table in schema_map.tables:
                for fk in table.foreign_keys:
                    child_table = table.name
                    parent_table = fk.ref_table

                    join_conditions = [
                        f"c.{quote_ident(c_col)} = p.{quote_ident(p_col)}"
                        for c_col, p_col in zip(fk.columns, fk.ref_columns)
                    ]
                    null_checks = [
                        f"p.{quote_ident(p_col)} IS NULL"
                        for p_col in fk.ref_columns
                    ]

                    # Only count rows where child FK value is not NULL
                    fk_not_null = " AND ".join(f"c.{quote_ident(c_col)} IS NOT NULL" for c_col in fk.columns)

                    sql = f"""
                        SELECT count(*)
                        FROM {quote_ident(child_table)} c
                        LEFT JOIN {quote_ident(parent_table)} p
                          ON {' AND '.join(join_conditions)}
                        WHERE ({' OR '.join(null_checks)})
                          AND ({fk_not_null});
                    """

                    cur.execute(sql)
                    orphan_count = cur.fetchone()[0]
                    passed = orphan_count == 0

                    results.append(
                        CheckResult(
                            name="orphans",
                            table=child_table,
                            passed=passed,
                            expected="0 orphans",
                            actual=f"{orphan_count} orphans",
                            details=f"FK {child_table}.{fk.columns} -> {parent_table}.{fk.ref_columns} has {orphan_count} orphaned records.",
                        )
                    )

    return results
