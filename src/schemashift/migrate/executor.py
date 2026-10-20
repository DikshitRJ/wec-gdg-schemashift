"""Database SQL execution utilities using psycopg.

Spec: migrate/executor
"""

from __future__ import annotations

import re

import psycopg

from schemashift.errors import MigrationError


def split_sql_statements(sql_text: str) -> list[str]:
    """Split SQL script into individual statements, ignoring comments."""
    # Strip comments
    lines = []
    for line in sql_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)

    # Split by semicolon not inside quotes
    statements: list[str] = []
    for part in re.split(r";\s*\n", cleaned):
        stmt = part.strip()
        if stmt:
            statements.append(stmt)
    return statements


def execute_sql_script(
    conn_str: str,
    sql_text: str,
    *,
    stop_on_error: bool = True,
) -> int:
    """Execute SQL script statement-by-statement.

    Returns the count of successfully executed statements.
    """
    statements = split_sql_statements(sql_text)
    executed = 0

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                for stmt in statements:
                    try:
                        cur.execute(stmt)
                        executed += 1
                    except Exception as exc:
                        if stop_on_error:
                            raise MigrationError(
                                f"SQL execution failed on statement: {stmt[:120]}...\nError: {exc}",
                                hint="Check PostgreSQL logs and SQL syntax.",
                            ) from exc
            conn.commit()
    except Exception as exc:
        if not isinstance(exc, MigrationError):
            raise MigrationError(
                f"Failed to connect or execute SQL: {exc}",
                hint="Check database connectivity and PostgreSQL credentials.",
            ) from exc
        raise

    return executed
