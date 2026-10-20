"""Graph runner exposing run, resume, and streaming event updates.

Spec: orchestration/runner
"""

from __future__ import annotations

import uuid
from typing import Any, Generator
from langgraph.types import Command

from schemashift.contracts.state import GraphState
from schemashift.graph.build import build_graph
from schemashift.graph.checkpoint import get_sqlite_checkpointer


class MigrationRunner:
    """Orchestrates running and resuming the migration graph."""

    def __init__(
        self,
        checkpoint_path: str = "workspace/out/state/checkpoints.sqlite",
    ) -> None:
        self.checkpointer = get_sqlite_checkpointer(checkpoint_path)
        self.app = build_graph(self.checkpointer)

    def run(
        self,
        *,
        config_path: str = "workspace/schemashift.yaml",
        ci_mode: bool = False,
        provider: str = "none",
        run_id: str | None = None,
    ) -> Generator[dict[str, Any], None, GraphState]:
        """Run the migration pipeline from the beginning, streaming step events."""
        run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
        thread_cfg = {"configurable": {"thread_id": run_id}}

        initial_state: GraphState = {
            "config_path": config_path,
            "ci_mode": ci_mode,
            "provider": provider,
            "run_id": run_id,
            "map_version": 1,
            "remap_attempts": 0,
        }

        final_state: GraphState = {}
        for event in self.app.stream(initial_state, config=thread_cfg, stream_mode="updates"):
            yield {"event": "update", "run_id": run_id, "data": event}

        # Check final state after stream
        state_snapshot = self.app.get_state(thread_cfg)
        final_state = state_snapshot.values if state_snapshot else {}
        yield {"event": "complete", "run_id": run_id, "state": final_state}
        return final_state

    def resume(
        self,
        run_id: str,
        *,
        action: str = "approve",
        overrides: list[dict[str, Any]] | None = None,
    ) -> Generator[dict[str, Any], None, GraphState]:
        """Resume a suspended graph execution from an interrupt."""
        thread_cfg = {"configurable": {"thread_id": run_id}}

        resume_payload = {
            "action": action,
            "overrides": overrides or [],
        }

        command = Command(resume=resume_payload)
        for event in self.app.stream(command, config=thread_cfg, stream_mode="updates"):
            yield {"event": "update", "run_id": run_id, "data": event}

        state_snapshot = self.app.get_state(thread_cfg)
        final_state = state_snapshot.values if state_snapshot else {}
        yield {"event": "complete", "run_id": run_id, "state": final_state}
        return final_state
