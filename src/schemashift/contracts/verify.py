"""Verification report contracts.

Spec: foundation/verify-models
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckResult(BaseModel, extra="forbid"):
    """Result of a single verification check."""

    name: str  # counts | checksums | spotcheck | orphans
    table: str = ""
    passed: bool = True
    expected: str = ""
    actual: str = ""
    details: str = ""


class VerifyReport(BaseModel, extra="forbid"):
    """Aggregated verification report."""

    passed: bool = True
    checks: list[CheckResult] = Field(default_factory=list)
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
