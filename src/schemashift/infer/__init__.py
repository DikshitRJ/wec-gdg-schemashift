"""Inference module re-exports.

Spec: infer/init
"""

from schemashift.infer.build import build_draft_map
from schemashift.infer.keys import detect_indexes_and_uniques
from schemashift.infer.nesting import NestingStrategy, decide_nesting_strategy
from schemashift.infer.references import detect_foreign_keys
from schemashift.infer.rules import RuleRegistry
from schemashift.infer.typemap import select_pg_type_and_transform

__all__ = [
    "NestingStrategy",
    "RuleRegistry",
    "build_draft_map",
    "decide_nesting_strategy",
    "detect_foreign_keys",
    "detect_indexes_and_uniques",
    "select_pg_type_and_transform",
]
