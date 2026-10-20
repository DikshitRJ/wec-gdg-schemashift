"""Inspection: profile a MongoDB source via sampling and field analysis.

Spec: inspection/init
"""

from schemashift.inspection.profile import build_profile, write_profile
from schemashift.inspection.redact import redact_examples
from schemashift.inspection.sampler import sample_collection
from schemashift.inspection.typestats import compute_field_stats

__all__ = [
    "build_profile",
    "compute_field_stats",
    "redact_examples",
    "sample_collection",
    "write_profile",
]
