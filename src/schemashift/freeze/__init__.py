"""Freeze module re-exports.

Spec: freeze-gate/init
"""

from schemashift.freeze.canonical import canonical_json, compute_map_hash
from schemashift.freeze.freezer import freeze_map, load_frozen_map
from schemashift.freeze.gate import GateItem, GateReport, evaluate_gate
from schemashift.freeze.overrides import apply_overrides, load_overrides

__all__ = [
    "GateItem",
    "GateReport",
    "apply_overrides",
    "canonical_json",
    "compute_map_hash",
    "evaluate_gate",
    "freeze_map",
    "load_frozen_map",
    "load_overrides",
]
