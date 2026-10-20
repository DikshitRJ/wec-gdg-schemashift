"""Similarity report and explanation nodes.

Spec: orchestration/node-similarity
"""

from __future__ import annotations

import json
from pathlib import Path

from schemashift.assist.explain_similarity import explain_similarity
from schemashift.config import Settings
from schemashift.contracts.profile import SourceProfile
from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.similarity import SimilarityReport
from schemashift.contracts.state import GraphState
from schemashift.llm.client import get_llm_client
from schemashift.similarity.report import (
    build_similarity_report,
    render_similarity_json,
    render_similarity_markdown,
)


def similarity_report_node(state: GraphState) -> GraphState:
    """Deterministic node: compute similarity scores and generate report."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)

    prof_data = json.loads(Path(state["profile_path"]).read_text(encoding="utf-8"))
    profile = SourceProfile.model_validate(prof_data)

    map_data = json.loads(Path(state["draft_map_path"]).read_text(encoding="utf-8"))
    schema_map = SchemaMap.model_validate(map_data)

    report = build_similarity_report(profile, schema_map, settings.scoring)

    out_dir = Path(settings.paths.out)
    json_path = out_dir / "reports" / "similarity.json"
    md_path = out_dir / "reports" / "similarity.md"

    render_similarity_json(report, json_path)
    render_similarity_markdown(report, md_path)

    return {
        "current_node": "similarity_report",
        "node_type": "D",
        "similarity_path": str(json_path.resolve()),
        "overall_score": report.overall_score,
    }


def explain_similarity_node(state: GraphState) -> GraphState:
    """Non-deterministic assist node: LLM explains alignment and ambiguous pairs."""
    config_path = state.get("config_path", "workspace/schemashift.yaml")
    settings = Settings.load(config_path)
    if state.get("provider"):
        settings.llm.provider = state["provider"]

    llm_client = get_llm_client(settings.llm)

    rep_data = json.loads(Path(state["similarity_path"]).read_text(encoding="utf-8"))
    report = SimilarityReport.model_validate(rep_data)

    explain_similarity(report, llm_client, out_dir=settings.paths.out)

    return {
        "current_node": "explain_similarity",
        "node_type": "ND",
    }
