"""LLM suggest and deterministic merge nodes.

Spec: orchestration/node-suggest
"""

from __future__ import annotations

import json
from pathlib import Path

from schemashift.assist.merge import merge_proposals
from schemashift.assist.suggest_schema import suggest_schema
from schemashift.config import Settings
from schemashift.contracts.profile import SourceProfile
from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.state import GraphState
from schemashift.freeze.overrides import apply_overrides, load_overrides
from schemashift.llm.client import get_llm_client


def suggest_schema_node(state: GraphState) -> GraphState:
    """Non-deterministic assist node: LLM suggests naming/relation improvements."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)
    if state.get("provider"):
        settings.llm.provider = state["provider"]

    llm_client = get_llm_client(settings.llm)

    prof_data = json.loads(Path(state["profile_path"]).read_text(encoding="utf-8"))
    profile = SourceProfile.model_validate(prof_data)

    proposals = suggest_schema(profile, llm_client)

    # Save proposals to reports/proposals.json
    out_dir = Path(settings.paths.out) / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    prop_file = out_dir / "proposals.json"
    prop_file.write_text(proposals.model_dump_json(indent=2) + "\n", encoding="utf-8")

    return {
        "current_node": "suggest_schema",
        "node_type": "ND",
        "proposals_path": str(prop_file.resolve()),
    }


def merge_proposals_node(state: GraphState) -> GraphState:
    """Deterministic node: validate/merge LLM proposals and user overrides."""
    import json

    from schemashift.contracts.llm import SchemaProposal

    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    map_data = json.loads(Path(state["draft_map_path"]).read_text(encoding="utf-8"))
    schema_map = SchemaMap.model_validate(map_data)

    # 1. Merge LLM proposals
    if state.get("proposals_path") and Path(state["proposals_path"]).exists():
        prop_data = json.loads(Path(state["proposals_path"]).read_text(encoding="utf-8"))
        proposals = SchemaProposal.model_validate(prop_data)
        schema_map = merge_proposals(schema_map, proposals)

    # 2. Apply user overrides from file or state
    file_overrides = load_overrides(settings.overrides_file)
    state_overrides = state.get("overrides", [])
    combined_overrides = file_overrides + state_overrides
    schema_map = apply_overrides(schema_map, combined_overrides)

    # Re-save updated draft map
    draft_file = Path(state["draft_map_path"])
    draft_file.write_text(schema_map.model_dump_json(indent=2) + "\n", encoding="utf-8")

    return {
        "current_node": "merge_proposals",
        "node_type": "D",
    }
