"""Annotate migration scripts with human-readable risk notes.

Spec: llm-assist/annotate-scripts
"""

from __future__ import annotations

from pathlib import Path
from schemashift.assist.fallbacks import fallback_annotate_scripts
from schemashift.contracts.llm import ScriptAnnotation
from schemashift.contracts.schema_map import SchemaMap
from schemashift.llm.client import LLMClient


def annotate_scripts(
    schema_map: SchemaMap,
    llm_client: LLMClient,
    out_dir: str | Path = "workspace/out",
) -> ScriptAnnotation:
    """Draft comments and risk notes for migration scripts in migrations/NOTES.md."""
    prompt = (
        f"Review this target SQL schema with tables {[t.name for t in schema_map.tables]}.\n"
        "Highlight potential migration risks (e.g. data loss, foreign key ordering, type truncations).\n"
        "Return ScriptAnnotation JSON."
    )

    annotation = llm_client.complete(prompt, ScriptAnnotation)
    if not annotation or not annotation.notes:
        annotation = fallback_annotate_scripts(schema_map)

    # Write migrations/NOTES.md sidecar
    p = Path(out_dir) / "migrations" / "NOTES.md"
    p.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Migration Risk & Script Notes",
        "",
        f"**Risk Level:** `{annotation.risk_level.upper()}`",
        f"**Summary:** {annotation.summary}",
        "",
        "## Key Observations",
    ]
    for note in annotation.notes:
        lines.append(f"- {note}")
    lines.append("")

    p.write_text("\n".join(lines), encoding="utf-8")
    return annotation
