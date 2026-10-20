"""Conditional routing functions for LangGraph pipeline.

Spec: orchestration/routing
"""

from __future__ import annotations

from typing import Literal
from schemashift.contracts.state import GraphState


def route_after_migrate(state: GraphState) -> Literal["verify", "diagnose_failures"]:
    """Route to verify if migration succeeded, else diagnose failures."""
    if state.get("migration_ok", False):
        return "verify"
    return "diagnose_failures"


def route_after_remap(state: GraphState) -> Literal["merge_proposals", "rollback"]:
    """Route back to merge proposals if remap attempts left, else rollback."""
    attempts = state.get("remap_attempts", 0)
    max_attempts = state.get("max_remap_attempts", 2)
    if attempts <= max_attempts and state.get("overrides"):
        return "merge_proposals"
    return "rollback"


def route_after_verify(state: GraphState) -> Literal["generate_orm", "rollback"]:
    """Route to ORM generation if verification passed, else rollback."""
    if state.get("verify_passed", False):
        return "generate_orm"
    return "rollback"
