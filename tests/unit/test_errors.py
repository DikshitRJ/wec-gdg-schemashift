"""Unit tests for errors.

Spec: foundation/errors-test
"""

from schemashift.errors import (
    ConfigurationError,
    FreezeError,
    GateRejectedError,
    LLMCacheMiss,
    MigrationError,
    SchemaShiftError,
    VerificationError,
)


def test_error_exit_codes_and_hints():
    e1 = ConfigurationError("bad config")
    assert e1.exit_code == 5
    assert "schemashift.yaml" in e1.hint

    e2 = GateRejectedError("gate rejected")
    assert e2.exit_code == 2

    e3 = VerificationError("verify failed")
    assert e3.exit_code == 3

    e4 = MigrationError("migration failed")
    assert e4.exit_code == 4

    e5 = LLMCacheMiss("cache miss")
    assert e5.exit_code == 6

    e6 = FreezeError("tampered")
    assert e6.exit_code == 6


def test_custom_hint_and_exit_code():
    e = SchemaShiftError("custom", hint="do this", exit_code=42)
    assert e.hint == "do this"
    assert e.exit_code == 42
