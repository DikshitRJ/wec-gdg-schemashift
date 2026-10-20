"""Summarize post-migration verification drift and probable causes.

Spec: llm-assist/drift-summary
"""

from __future__ import annotations

from pathlib import Path
from schemashift.assist.fallbacks import fallback_drift_summary
from schemashift.contracts.llm import ExplanationNote
from schemashift.contracts.verify import VerifyReport
from schemashift.llm.client import LLMClient


def summarize_drift(
    report: VerifyReport,
    llm_client: LLMClient,
    out_dir: str | Path = "workspace/out",
) -> str:
    """Summarize verification drift and write reports/drift.md."""
    if report.passed:
        text = fallback_drift_summary(report)
    else:
        failed_checks = [c.model_dump() for c in report.checks if not c.passed]
        prompt = (
            f"Verification failed on these checks:\n{failed_checks}\n"
            "Explain likely causes and remediation steps. Return ExplanationNote JSON."
        )
        note = llm_client.complete(prompt, ExplanationNote)
        text = note.text if note and note.text else fallback_drift_summary(report)

    # Write reports/drift.md
    p = Path(out_dir) / "reports" / "drift.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"# Post-Migration Verification & Drift Summary\n\n{text}\n", encoding="utf-8")
    return text
