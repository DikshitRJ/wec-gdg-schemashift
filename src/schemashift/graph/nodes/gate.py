"""Approval and remap human-in-the-loop gate nodes.

Spec: orchestration/node-gate
"""

from __future__ import annotations

import json
from pathlib import Path

from langgraph.types import interrupt

from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.similarity import SimilarityReport
from schemashift.contracts.state import GraphState
from schemashift.errors import GateRejectedError
from schemashift.freeze.gate import evaluate_gate


def approval_gate_node(state: GraphState) -> GraphState:
    """Deterministic human-in-the-loop approval gate node."""
    ci_mode = state.get("ci_mode", False)

    map_data = json.loads(Path(state["draft_map_path"]).read_text(encoding="utf-8"))
    schema_map = SchemaMap.model_validate(map_data)

    rep_data = json.loads(Path(state["similarity_path"]).read_text(encoding="utf-8"))
    similarity_report = SimilarityReport.model_validate(rep_data)

    gate_eval = evaluate_gate(schema_map, similarity_report, ci_mode=ci_mode)

    if not gate_eval.passed and not ci_mode:
        # HITL interrupt: passes gate evaluation details to the UI/runner
        gate_input = interrupt(
            {
                "type": "approval_gate",
                "items": [it.model_dump() for it in gate_eval.items],
                "overall_score": similarity_report.overall_score,
                "overall_band": similarity_report.overall_band.value,
            }
        )

        # Process user decision from interrupt resume
        if isinstance(gate_input, dict):
            action = gate_input.get("action", "approve")
            if action == "reject":
                raise GateRejectedError("Gate approval was rejected by human operator.")
            overrides = gate_input.get("overrides", [])
            return {
                "current_node": "approval_gate",
                "node_type": "D",
                "gate_approved": True,
                "overrides": overrides,
            }

    elif not gate_eval.passed and ci_mode:
        raise GateRejectedError(
            f"Gate check failed in CI mode with {gate_eval.blocked_count} blocked item(s).",
            hint="Resolve low-confidence mappings with an entry in overrides.yaml.",
        )

    return {
        "current_node": "approval_gate",
        "node_type": "D",
        "gate_approved": True,
    }


def remap_gate_node(state: GraphState) -> GraphState:
    """Deterministic human-in-the-loop remap gate node on migration failure."""
    ci_mode = state.get("ci_mode", False)
    remap_attempts = state.get("remap_attempts", 0) + 1
    max_remap_attempts = state.get("max_remap_attempts", 2)

    if remap_attempts > max_remap_attempts:
        return {
            "current_node": "remap_gate",
            "node_type": "D",
            "migration_ok": False,
            "remap_attempts": remap_attempts,
        }

    if not ci_mode:
        # Interrupt to ask reviewer whether to apply suggested patch
        gate_input = interrupt(
            {
                "type": "remap_gate",
                "attempt": remap_attempts,
                "max_attempts": max_remap_attempts,
            }
        )
        if isinstance(gate_input, dict) and gate_input.get("action") == "abort":
            return {
                "current_node": "remap_gate",
                "node_type": "D",
                "migration_ok": False,
                "remap_attempts": remap_attempts,
            }

    return {
        "current_node": "remap_gate",
        "node_type": "D",
        "remap_attempts": remap_attempts,
    }
