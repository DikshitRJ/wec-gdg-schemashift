"""SchemaShift error taxonomy with actionable hints and exit codes.

Spec: foundation/errors
"""

from __future__ import annotations


class SchemaShiftError(Exception):
    """Base error for SchemaShift with an actionable hint and exit code."""

    exit_code: int = 6
    hint: str = ""

    def __init__(self, message: str, *, hint: str = "", exit_code: int | None = None):
        super().__init__(message)
        self.hint = hint or self.__class__.hint
        if exit_code is not None:
            self.exit_code = exit_code


class ConfigurationError(SchemaShiftError):
    """Configuration is invalid or missing."""

    exit_code = 5
    hint = "Check workspace/schemashift.yaml and environment variables."


class GateRejectedError(SchemaShiftError):
    """Gate rejected or needs_review unresolved."""

    exit_code = 2
    hint = "Review the gate report and provide overrides or approvals."


class VerificationError(SchemaShiftError):
    """Post-migration verification failed."""

    exit_code = 3
    hint = "Check reports/verify.json for failed checks. Rollback may be needed."


class MigrationError(SchemaShiftError):
    """Data migration failed."""

    exit_code = 4
    hint = "Check reports/failures.json for row-level errors."


class LLMCacheMiss(SchemaShiftError):
    """Replay provider encountered a cache miss."""

    exit_code = 6
    hint = "Run with provider=openai first to populate the cache."


class FreezeError(SchemaShiftError):
    """Schema map freeze or verification failed."""

    exit_code = 6
    hint = "The frozen map may have been tampered with. Re-run the pipeline."


class InternalError(SchemaShiftError):
    """Unexpected internal error."""

    exit_code = 6
    hint = "This is a bug. Please report it."
