"""Freeze and script generation nodes.

Spec: orchestration/node-freeze-gen
"""

from __future__ import annotations

import json
from pathlib import Path
from schemashift.assist.annotate_scripts import annotate_scripts
from schemashift.config import Settings
from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.state import GraphState
from schemashift.freeze.freezer import freeze_map, load_frozen_map
from schemashift.gen.ddl import write_ddl
from schemashift.gen.etl_plan import write_etl_artifacts
from schemashift.gen.rollback import write_rollback
from schemashift.llm.client import get_llm_client


def freeze_map_node(state: GraphState) -> GraphState:
    """Deterministic node: freeze draft schema map, verify and write to out/."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    draft_path = Path(state["draft_map_path"])
    schema_map = SchemaMap.model_validate(json.loads(draft_path.read_text(encoding="utf-8")))

    # Bump version if re-freezing
    current_version = state.get("map_version", 1)
    schema_map.map_version = current_version

    frozen_map, frozen_path = freeze_map(schema_map, settings.paths.out)

    return {
        "current_node": "freeze_map",
        "node_type": "D",
        "frozen_map_path": frozen_path,
        "map_hash": frozen_map.map_hash,
        "map_version": frozen_map.map_version,
    }


def generate_scripts_node(state: GraphState) -> GraphState:
    """Deterministic node: generate DDL, rollback, and ETL scripts from frozen map."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    # Must load and verify frozen map hash
    frozen_map = load_frozen_map(state["frozen_map_path"])

    out_dir = Path(settings.paths.out)
    mig_dir = out_dir / "migrations"
    mig_dir.mkdir(parents=True, exist_ok=True)

    ddl_path = mig_dir / "001_schema.sql"
    rollback_path = mig_dir / "001_schema.down.sql"

    write_ddl(frozen_map, ddl_path)
    write_rollback(frozen_map, rollback_path)
    etl_plan_path, _ = write_etl_artifacts(frozen_map, out_dir)

    return {
        "current_node": "generate_scripts",
        "node_type": "D",
        "ddl_path": str(ddl_path.resolve()),
        "rollback_path": str(rollback_path.resolve()),
        "etl_plan_path": etl_plan_path,
    }


def annotate_scripts_node(state: GraphState) -> GraphState:
    """Non-deterministic assist node: draft migration comments and risk notes."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)
    if state.get("provider"):
        settings.llm.provider = state["provider"]

    llm_client = get_llm_client(settings.llm)
    frozen_map = load_frozen_map(state["frozen_map_path"])

    annotate_scripts(frozen_map, llm_client, out_dir=settings.paths.out)

    return {
        "current_node": "annotate_scripts",
        "node_type": "ND",
    }
