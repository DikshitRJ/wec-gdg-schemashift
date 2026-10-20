"""LangGraph state definition.

Spec: foundation/state
"""

from __future__ import annotations

from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    """State passed through the LangGraph pipeline.

    Holds only small scalars, file paths, and hashes.
    Heavy data (profiles, maps, reports) live in workspace/out/.
    """

    # Config
    config_path: str
    run_id: str
    ci_mode: bool
    provider: str

    # Paths to persisted artifacts
    profile_path: str
    draft_map_path: str
    proposals_path: str
    similarity_path: str
    frozen_map_path: str
    ddl_path: str
    rollback_path: str
    etl_plan_path: str
    verify_path: str
    orm_dir: str
    failures_path: str

    # State
    map_hash: str
    map_version: int
    overall_score: float
    gate_approved: bool
    gate_payload: dict[str, Any]
    overrides: list[dict[str, Any]]
    migration_ok: bool
    verify_passed: bool
    remap_attempts: int
    max_remap_attempts: int

    # Events for TUI
    current_node: str
    node_type: str  # D | ND
    progress: dict[str, Any]
    error: str
