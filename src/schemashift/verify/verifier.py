"""Aggregated verification runner producing VerifyReport.

Spec: verify/verifier
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pymongo import MongoClient

from schemashift.contracts.schema_map import SchemaMap
from schemashift.contracts.verify import CheckResult, VerifyReport
from schemashift.verify.checksums import verify_checksums
from schemashift.verify.counts import verify_counts
from schemashift.verify.orphans import verify_orphans
from schemashift.verify.spotcheck import spotcheck_records


def run_verification(
    mongo_uri: str,
    pg_uri: str,
    schema_map: SchemaMap,
    *,
    out_dir: str = "workspace/out",
) -> VerifyReport:
    """Run all verification suites and persist report."""
    mongo_client: MongoClient[dict[str, Any]] = MongoClient(mongo_uri)

    checks: list[CheckResult] = []

    # 1. Record counts
    checks.extend(verify_counts(mongo_client, pg_uri, schema_map))

    # 2. Orphan check
    checks.extend(verify_orphans(pg_uri, schema_map))

    # 3. Checksums
    checks.extend(verify_checksums(pg_uri, schema_map))

    # 4. Spot check
    checks.extend(spotcheck_records(mongo_client, pg_uri, schema_map))

    passed_checks = sum(1 for c in checks if c.passed)
    failed_checks = sum(1 for c in checks if not c.passed)
    all_passed = failed_checks == 0

    report = VerifyReport(
        passed=all_passed,
        checks=checks,
        total_checks=len(checks),
        passed_checks=passed_checks,
        failed_checks=failed_checks,
    )

    # Persist report
    p = Path(out_dir) / "reports" / "verify.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")

    return report
