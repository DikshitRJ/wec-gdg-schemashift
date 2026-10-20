"""Similarity report generation (JSON and Markdown).

Spec: similarity/report
"""

from __future__ import annotations

from pathlib import Path

from schemashift.config import ScoringConfig
from schemashift.contracts.profile import SourceProfile
from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.similarity import (
    Band,
    EntityScore,
    FieldScore,
    SimilarityReport,
)
from schemashift.similarity.matcher import pair_fields
from schemashift.similarity.scoring import score_field


def build_similarity_report(
    profile: SourceProfile,
    schema_map: SchemaMap,
    config: ScoringConfig,
) -> SimilarityReport:
    """Build a comprehensive similarity report."""
    pairs = pair_fields(profile, schema_map)

    # Group pairs by collection
    pairs_by_coll: dict[str, list] = {}
    for pair in pairs:
        coll = pair.collection
        if coll not in pairs_by_coll:
            pairs_by_coll[coll] = []
        pairs_by_coll[coll].append(pair)

    entity_scores: list[EntityScore] = []
    all_field_scores: list[FieldScore] = []

    for coll_name in sorted(pairs_by_coll.keys()):
        coll_pairs = pairs_by_coll[coll_name]
        field_scores: list[FieldScore] = []
        matched_tables: set[str] = set()

        for p in coll_pairs:
            fs = score_field(p.field, p.column, p.table, config)
            field_scores.append(fs)
            all_field_scores.append(fs)
            if p.table:
                matched_tables.add(p.table.name)

        field_count = len(field_scores)
        total_entity_score = (
            sum(fs.total for fs in field_scores) / field_count if field_count > 0 else 0.0
        )

        matched_cnt = sum(1 for fs in field_scores if fs.band == Band.MATCHED)
        guessed_cnt = sum(1 for fs in field_scores if fs.band == Band.GUESSED)
        needs_review_cnt = sum(1 for fs in field_scores if fs.band == Band.NEEDS_REVIEW)

        entity_scores.append(
            EntityScore(
                collection=coll_name,
                tables=sorted(matched_tables),
                field_scores=field_scores,
                total=round(total_entity_score, 4),
                field_count=field_count,
                matched_count=matched_cnt,
                guessed_count=guessed_cnt,
                needs_review_count=needs_review_cnt,
            )
        )

    # Compute overall score
    total_fields = sum(es.field_count for es in entity_scores)
    if total_fields > 0:
        overall_score = round(
            sum(es.total * es.field_count for es in entity_scores) / total_fields, 4
        )
    else:
        overall_score = 0.0

    if overall_score >= config.matched:
        overall_band = Band.MATCHED
    elif overall_score >= config.guessed:
        overall_band = Band.GUESSED
    else:
        overall_band = Band.NEEDS_REVIEW

    # Drag list: items with lowest score (highest drag on overall score)
    drag_list = sorted(
        [fs for fs in all_field_scores if fs.band != Band.MATCHED],
        key=lambda fs: fs.total,
    )

    matched_total = sum(es.matched_count for es in entity_scores)
    guessed_total = sum(es.guessed_count for es in entity_scores)
    needs_review_total = sum(es.needs_review_count for es in entity_scores)

    return SimilarityReport(
        overall_score=overall_score,
        overall_band=overall_band,
        entity_scores=entity_scores,
        drag_list=drag_list[:10],
        total_fields=total_fields,
        matched_fields=matched_total,
        guessed_fields=guessed_total,
        needs_review_fields=needs_review_total,
    )


def render_similarity_json(report: SimilarityReport, out_path: str | Path) -> None:
    """Save report as JSON."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")


def render_similarity_markdown(report: SimilarityReport, out_path: str | Path) -> None:
    """Render a human-readable Markdown report."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "# Database Schema Similarity Report",
        "",
        f"**Overall Match:** `{report.overall_score * 100:.1f}%` ({report.overall_band.value.upper()})",
        f"- Matched: `{report.matched_fields}`",
        f"- Guessed: `{report.guessed_fields}`",
        f"- Needs Review: `{report.needs_review_fields}`",
        "",
        "## Per-Entity Alignment",
        "",
        "| Collection | Target Tables | Match % | Fields | Matched | Guessed | Needs Review |",
        "|---|---|---|---|---|---|---|",
    ]

    for es in report.entity_scores:
        tables_str = ", ".join(es.tables) or "None"
        lines.append(
            f"| `{es.collection}` | `{tables_str}` | `{es.total * 100:.1f}%` | {es.field_count} | {es.matched_count} | {es.guessed_count} | {es.needs_review_count} |"
        )

    lines.extend(
        [
            "",
            "## Top Score Drags (Ambiguous / Divergent Fields)",
            "",
            "| Source Field | Target Column | Score | Band | Reasons |",
            "|---|---|---|---|---|",
        ]
    )

    for fs in report.drag_list:
        reasons = ", ".join(fs.reason_codes) or "None"
        lines.append(
            f"| `{fs.source_path}` | `{fs.target_table}.{fs.target_column}` | `{fs.total * 100:.1f}%` | `{fs.band.value}` | {reasons} |"
        )

    lines.append("")
    p.write_text("\n".join(lines), encoding="utf-8")
