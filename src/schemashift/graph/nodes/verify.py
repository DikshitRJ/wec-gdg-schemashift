"""Verification, drift summary, and rollback nodes.

Spec: orchestration/node-verify
"""

from __future__ import annotations

import contextlib
from pathlib import Path

from schemashift.assist.drift_summary import summarize_drift
from schemashift.config import Settings
from schemashift.contracts.state import GraphState
from schemashift.freeze.freezer import load_frozen_map
from schemashift.llm.client import get_llm_client
from schemashift.migrate.executor import execute_sql_script
from schemashift.verify.verifier import run_verification


def verify_node(state: GraphState) -> GraphState:
    """Deterministic node: execute counts, checksums, spotcheck, and orphan scans."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    frozen_map = load_frozen_map(state["frozen_map_path"])

    report = run_verification(
        mongo_uri=settings.source.uri,
        pg_uri=settings.target.uri,
        schema_map=frozen_map,
        out_dir=settings.paths.out,
    )

    out_file = Path(settings.paths.out) / "reports" / "verify.json"

    return {
        "current_node": "verify",
        "node_type": "D",
        "verify_passed": report.passed,
        "verify_path": str(out_file.resolve()),
    }


def drift_summary_node(state: GraphState) -> GraphState:
    """Non-deterministic assist node: explain verification drift."""
    import json

    from schemashift.contracts.verify import VerifyReport

    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)
    if state.get("provider"):
        settings.llm.provider = state["provider"]

    llm_client = get_llm_client(settings.llm)

    rep_data = json.loads(Path(state["verify_path"]).read_text(encoding="utf-8"))
    report = VerifyReport.model_validate(rep_data)

    summarize_drift(report, llm_client, out_dir=settings.paths.out)

    return {
        "current_node": "drift_summary",
        "node_type": "ND",
    }


def rollback_node(state: GraphState) -> GraphState:
    """Deterministic node: drop target tables upon fatal failure."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    if state.get("rollback_path"):
        down_sql = Path(state["rollback_path"]).read_text(encoding="utf-8")
        with contextlib.suppress(Exception):
            execute_sql_script(settings.target.uri, down_sql, stop_on_error=False)

    return {
        "current_node": "rollback",
        "node_type": "D",
    }
