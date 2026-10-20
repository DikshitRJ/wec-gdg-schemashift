"""Source loading, sampling, and inference nodes.

Spec: orchestration/node-source
"""

from __future__ import annotations

from pathlib import Path
from pymongo import MongoClient

from schemashift.config import Settings
from schemashift.contracts.state import GraphState
from schemashift.infer.build import build_draft_map
from schemashift.inspection.profile import build_profile, write_profile


def load_config_node(state: GraphState) -> GraphState:
    """Deterministic node: load settings from config path."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    # Provider override from state if passed
    if state.get("provider"):
        settings.llm.provider = state["provider"]

    return {
        "current_node": "load_config",
        "node_type": "D",
        "max_remap_attempts": settings.migration.max_remap_attempts,
        "remap_attempts": state.get("remap_attempts", 0),
    }


def sample_source_node(state: GraphState) -> GraphState:
    """Deterministic node: sample MongoDB source and write profile."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    mongo_client = MongoClient(settings.source.uri)
    profile = build_profile(
        mongo_client,
        settings.source.database,
        settings.sampling.size,
    )

    out_dir = settings.paths.out
    prof_path = write_profile(profile, out_dir)

    return {
        "current_node": "sample_source",
        "node_type": "D",
        "profile_path": prof_path,
    }


def infer_candidates_node(state: GraphState) -> GraphState:
    """Deterministic node: run rule-based schema inference."""
    import json
    from schemashift.contracts.profile import SourceProfile

    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    prof_data = json.loads(Path(state["profile_path"]).read_text(encoding="utf-8"))
    profile = SourceProfile.model_validate(prof_data)

    draft_map = build_draft_map(profile, settings)

    # Save draft map to reports/inference.json
    out_dir = Path(settings.paths.out) / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    draft_file = out_dir / "inference.json"
    draft_file.write_text(draft_map.model_dump_json(indent=2) + "\n", encoding="utf-8")

    return {
        "current_node": "infer_candidates",
        "node_type": "D",
        "draft_map_path": str(draft_file.resolve()),
    }
