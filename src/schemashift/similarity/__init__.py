"""Similarity module re-exports.

Spec: similarity/init
"""

from schemashift.similarity.matcher import MatchedPair, pair_fields
from schemashift.similarity.report import (
    build_similarity_report,
    render_similarity_json,
    render_similarity_markdown,
)
from schemashift.similarity.scoring import score_field

__all__ = [
    "MatchedPair",
    "build_similarity_report",
    "pair_fields",
    "render_similarity_json",
    "render_similarity_markdown",
    "score_field",
]
