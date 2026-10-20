"""Unit tests for the inspection module.

Spec: inspect/unit-test
"""

from bson import ObjectId

from schemashift.contracts.profile import FieldProfile
from schemashift.inspection.redact import redact_examples
from schemashift.inspection.typestats import compute_field_stats


def test_compute_field_stats():
    docs = [
        {
            "_id": ObjectId(),
            "name": "Alice",
            "age": 30,
            "tags": ["vip", "early"],
            "address": {"city": "Springfield", "geo": {"lat": 40.0, "lng": -74.0}},
        },
        {
            "_id": ObjectId(),
            "name": "Bob",
            "age": 25,
            "tags": ["vip"],
            "address": {"city": "Riverdale", "geo": {"lat": 41.0, "lng": -73.0}},
        },
    ]

    profiles = compute_field_stats(docs, "users")
    paths = {p.path: p for p in profiles}

    assert "_id" in paths
    assert "name" in paths
    assert paths["name"].types == {"string": 2}
    assert paths["name"].presence_rate == 1.0

    assert "tags[]" in paths
    assert paths["tags[]"].types == {"string": 3}

    assert "address.city" in paths
    assert "address.geo.lat" in paths


def test_redact_examples():
    fp = FieldProfile(
        path="users.secret",
        types={"string": 1},
        presence_rate=1.0,
        examples=["short", "a-very-long-string-that-needs-hashing-because-it-exceeds-20-chars"],
    )
    redacted = redact_examples(fp)
    assert len(redacted.examples) == 2
    assert redacted.examples[0] == "short"
    assert str(redacted.examples[1]).startswith("hash:")
