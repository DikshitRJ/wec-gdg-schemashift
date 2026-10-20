"""Rule registry and Decision recording.

Spec: infer/rules
"""

from __future__ import annotations

from typing import Any

from schemashift.contracts.schema_map import Decision


class RuleRegistry:
    """Registry that collects decisions made during inference."""

    def __init__(self) -> None:
        self.decisions: list[Decision] = []
        self._count = 0

    def record_decision(
        self,
        *,
        rule: str,
        choice: str,
        alternatives: list[str] | None = None,
        evidence: dict[str, Any] | None = None,
        provenance: str = "rule",
        ambiguity: bool = False,
    ) -> Decision:
        """Record an inference decision with evidence."""
        self._count += 1
        d_id = f"D-{self._count:03d}"
        decision = Decision(
            id=d_id,
            rule=rule,
            choice=choice,
            alternatives=alternatives or [],
            evidence=evidence or {},
            provenance=provenance,
            ambiguity=ambiguity,
        )
        self.decisions.append(decision)
        return decision
