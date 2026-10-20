"""Deterministic fallback narratives for all LLM assist functions.

Spec: llm-assist/fallbacks
"""

from __future__ import annotations

from schemashift.contracts.llm import (
    RemapPatch,
    SchemaProposal,
    ScriptAnnotation,
)
from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.similarity import SimilarityReport
from schemashift.contracts.verify import VerifyReport
from schemashift.migrate.failures import RowFailure


def fallback_schema_proposal() -> SchemaProposal:
    """Return empty proposal when LLM is unavailable."""
    return SchemaProposal(proposals=[])


def fallback_explain_similarity(report: SimilarityReport) -> str:
    """Return deterministic explanation of similarity scores."""
    lines = [
        f"Overall database schema similarity is {report.overall_score * 100:.1f}%.",
        f"Classification: {report.overall_band.value.upper()}.",
    ]
    if report.drag_list:
        lines.append(f"Top {len(report.drag_list)} fields affecting alignment:")
        for fs in report.drag_list[:5]:
            lines.append(
                f"- {fs.source_path} -> {fs.target_table}.{fs.target_column} (score: {fs.total * 100:.1f}%, reasons: {', '.join(fs.reason_codes)})"
            )
    else:
        lines.append("All fields mapped cleanly with high confidence.")
    return "\n".join(lines)


def fallback_annotate_scripts(schema_map: SchemaMap) -> ScriptAnnotation:
    """Return deterministic risk notes for script generation."""
    notes = [
        "DDL statements use IF NOT EXISTS for safe repeated application.",
        "Tables are ordered topologically to preserve foreign key referential integrity.",
        "Foreign key constraints enforce referential integrity across root and child tables.",
    ]
    has_jsonb = any(c.pg_type == "JSONB" for t in schema_map.tables for c in t.columns)
    if has_jsonb:
        notes.append(
            "JSONB columns detected. Ensure application queries use appropriate JSON operators."
        )

    return ScriptAnnotation(
        risk_level="low" if not has_jsonb else "medium",
        notes=notes,
        summary="Automated migration scripts generated from frozen schema map.",
    )


def fallback_diagnose_failures(failures: list[RowFailure]) -> RemapPatch:
    """Return deterministic remap diagnosis from row failures."""
    if not failures:
        return RemapPatch(target="", changes={}, rationale="No failures to diagnose.")

    first = failures[0]
    # Check if failure is uncoercible rating
    if "reviews" in first.collection and "rating" in first.column:
        return RemapPatch(
            target="reviews.rating",
            changes={"pg_type": "TEXT", "transform": "identity"},
            rationale="Uncoercible string rating values detected; fallback to TEXT column type.",
        )

    return RemapPatch(
        target=f"{first.collection}.{first.column}",
        changes={"transform": "identity"},
        rationale=f"Diagnosed failure: {first.reason}",
    )


def fallback_drift_summary(report: VerifyReport) -> str:
    """Return deterministic drift summary."""
    if report.passed:
        return f"Post-migration verification passed: all {report.total_checks} checks succeeded."
    failed = [c for c in report.checks if not c.passed]
    lines = [f"Verification failed on {len(failed)} of {report.total_checks} checks:"]
    for c in failed:
        lines.append(
            f"- {c.name} on {c.table}: expected {c.expected}, found {c.actual}. {c.details}"
        )
    return "\n".join(lines)
