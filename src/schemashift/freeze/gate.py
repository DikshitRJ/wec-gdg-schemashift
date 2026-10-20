"""Approval gate evaluation and policy checking.

Spec: freeze-gate/gate
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.similarity import Band, SimilarityReport


class GateItem(BaseModel):
    """An item requiring gate review."""

    target: str
    reasons: list[str]
    band: str = "needs_review"
    can_auto_approve: bool = False


class GateReport(BaseModel):
    """Evaluation result from the approval gate."""

    passed: bool
    requires_approval: bool
    items: list[GateItem] = Field(default_factory=list)
    auto_approvable_count: int = 0
    blocked_count: int = 0


def evaluate_gate(
    schema_map: SchemaMap,
    similarity_report: SimilarityReport,
    *,
    ci_mode: bool = False,
) -> GateReport:
    """Evaluate whether schema map passes gate or requires human approval."""
    items: list[GateItem] = []

    # Check field scores from similarity report
    for es in similarity_report.entity_scores:
        for fs in es.field_scores:
            if fs.band == Band.NEEDS_REVIEW:
                items.append(
                    GateItem(
                        target=f"{fs.target_table}.{fs.target_column or fs.source_path}",
                        reasons=fs.reason_codes or [f"Band is {fs.band.value}"],
                        band=fs.band.value,
                        can_auto_approve=False,
                    )
                )
            elif fs.band == Band.GUESSED:
                items.append(
                    GateItem(
                        target=f"{fs.target_table}.{fs.target_column or fs.source_path}",
                        reasons=fs.reason_codes or [f"Band is {fs.band.value}"],
                        band=fs.band.value,
                        can_auto_approve=True,
                    )
                )

    # Check decisions with ambiguity or LLM structural changes
    for dec in schema_map.decisions:
        if dec.ambiguity:
            items.append(
                GateItem(
                    target=dec.choice,
                    reasons=[f"Rule: {dec.rule} (ambiguity=True)"],
                    band="guessed",
                    can_auto_approve=True,  # Gated but auto-approvable in CI as documented
                )
            )
        elif dec.provenance == "llm_proposed_validated":
            items.append(
                GateItem(
                    target=dec.choice,
                    reasons=[f"Rule: {dec.rule} (provenance=llm_proposed_validated)"],
                    band="guessed",
                    can_auto_approve=True,
                )
            )

    # Deduplicate items by target
    dedup: dict[str, GateItem] = {}
    for item in items:
        if item.target not in dedup:
            dedup[item.target] = item
        else:
            dedup[item.target].reasons.extend(item.reasons)

    final_items = list(dedup.values())
    auto_cnt = sum(1 for it in final_items if it.can_auto_approve)
    blocked_cnt = sum(1 for it in final_items if not it.can_auto_approve)

    if not final_items:
        return GateReport(
            passed=True,
            requires_approval=False,
            items=[],
            auto_approvable_count=0,
            blocked_count=0,
        )

    if ci_mode:
        if blocked_cnt > 0:
            return GateReport(
                passed=False,
                requires_approval=True,
                items=final_items,
                auto_approvable_count=auto_cnt,
                blocked_count=blocked_cnt,
            )
        else:
            return GateReport(
                passed=True,
                requires_approval=False,
                items=final_items,
                auto_approvable_count=auto_cnt,
                blocked_count=0,
            )

    return GateReport(
        passed=False,
        requires_approval=True,
        items=final_items,
        auto_approvable_count=auto_cnt,
        blocked_count=blocked_cnt,
    )
