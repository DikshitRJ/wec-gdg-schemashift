"""Assist module re-exports.

Spec: llm-assist/assist-init
"""

from schemashift.assist.annotate_scripts import annotate_scripts
from schemashift.assist.diagnose_failures import diagnose_failures
from schemashift.assist.drift_summary import summarize_drift
from schemashift.assist.explain_similarity import explain_similarity
from schemashift.assist.fallbacks import (
    fallback_annotate_scripts,
    fallback_diagnose_failures,
    fallback_drift_summary,
    fallback_explain_similarity,
    fallback_schema_proposal,
)
from schemashift.assist.merge import merge_proposals
from schemashift.assist.refactor_notes import generate_refactor_notes
from schemashift.assist.suggest_schema import suggest_schema

__all__ = [
    "annotate_scripts",
    "diagnose_failures",
    "explain_similarity",
    "fallback_annotate_scripts",
    "fallback_diagnose_failures",
    "fallback_drift_summary",
    "fallback_explain_similarity",
    "fallback_schema_proposal",
    "generate_refactor_notes",
    "merge_proposals",
    "suggest_schema",
    "summarize_drift",
]
