"""DDL application, data migration, and diagnosis nodes.

Spec: orchestration/node-migrate
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

from schemashift.assist.diagnose_failures import diagnose_failures
from schemashift.config import Settings
from schemashift.contracts.state import GraphState
from schemashift.errors import MigrationError
from schemashift.freeze.freezer import load_frozen_map
from schemashift.llm.client import get_llm_client
from schemashift.migrate.executor import execute_sql_script
from schemashift.migrate.failures import RowFailure
from schemashift.migrate.loader import DataLoader


def apply_ddl_node(state: GraphState) -> GraphState:
    """Deterministic node: apply DDL to PostgreSQL target."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    # If reset_target is enabled, run down script first to clean database
    if settings.target.reset_target and state.get("rollback_path"):
        down_sql = Path(state["rollback_path"]).read_text(encoding="utf-8")
        with contextlib.suppress(Exception):
            execute_sql_script(settings.target.uri, down_sql, stop_on_error=False)

    ddl_sql = Path(state["ddl_path"]).read_text(encoding="utf-8")
    execute_sql_script(settings.target.uri, ddl_sql, stop_on_error=True)

    return {
        "current_node": "apply_ddl",
        "node_type": "D",
    }


def migrate_data_node(state: GraphState) -> GraphState:
    """Deterministic node: batch load data into target PostgreSQL."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    frozen_map = load_frozen_map(state["frozen_map_path"])

    loader = DataLoader(
        mongo_uri=settings.source.uri,
        pg_uri=settings.target.uri,
        schema_map=frozen_map,
        batch_size=settings.migration.batch_size,
        truncate=True,
        out_dir=settings.paths.out,
    )

    try:
        results = loader.load_all()
        return {
            "current_node": "migrate_data",
            "node_type": "D",
            "migration_ok": True,
            "progress": results,
        }
    except MigrationError as me:
        return {
            "current_node": "migrate_data",
            "node_type": "D",
            "migration_ok": False,
            "error": str(me),
            "failures_path": str(
                (Path(settings.paths.out) / "reports" / "failures.json").resolve()
            ),
        }


def diagnose_failures_node(state: GraphState) -> GraphState:
    """Non-deterministic assist node: analyze failed rows and propose a remap patch."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)
    if state.get("provider"):
        settings.llm.provider = state["provider"]

    llm_client = get_llm_client(settings.llm)

    failures: list[RowFailure] = []
    fail_path = Path(state.get("failures_path", ""))
    if fail_path.exists():
        fail_data = json.loads(fail_path.read_text(encoding="utf-8"))
        failures = [RowFailure.model_validate(f) for f in fail_data.get("failures", [])]

    patch = diagnose_failures(failures, llm_client)

    # If patch suggests changes, convert to override format
    patch_overrides = []
    if patch.target and patch.changes:
        patch_overrides.append({"target": patch.target, "set": patch.changes})

    return {
        "current_node": "diagnose_failures",
        "node_type": "ND",
        "overrides": patch_overrides,
    }
