"""Generate explanations for similarity report and ambiguous pairs.

Spec: llm-assist/explain-similarity
"""

from __future__ import annotations

from pathlib import Path
from schemashift.assist.fallbacks import fallback_explain_similarity
from schemashift.contracts.llm import ExplanationNote
from schemashift.contracts.similarity import SimilarityReport
from schemashift.llm.client import LLMClient


def explain_similarity(
    report: SimilarityReport,
    llm_client: LLMClient,
    out_dir: str | Path = "workspace/out",
) -> str:
    """Generate narrative explanation of database similarity and write explanations.md."""
    prompt = (
        f"Explain why this database migration has a match percentage of {report.overall_score * 100:.1f}%.\n"
        f"Top drag fields: {[fs.source_path for fs in report.drag_list[:5]]}\n"
        "Return ExplanationNote JSON with section and text fields."
    )

    note = llm_client.complete(prompt, ExplanationNote)
    text = note.text if note and note.text else fallback_explain_similarity(report)

    # Write sidecar explanations.md
    p = Path(out_dir) / "reports" / "explanations.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"# Database Similarity Analysis\n\n{text}\n", encoding="utf-8")

    return text
