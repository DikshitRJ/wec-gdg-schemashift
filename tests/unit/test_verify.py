"""Unit tests for verify contracts and reporting.

Spec: verify/unit-test
"""

from schemashift.contracts.verify import CheckResult, VerifyReport


def test_verify_report():
    c1 = CheckResult(name="counts", table="users", passed=True, expected="200", actual="200")
    c2 = CheckResult(name="orphans", table="reviews", passed=True, expected="0", actual="0")

    report = VerifyReport(
        passed=True,
        checks=[c1, c2],
        total_checks=2,
        passed_checks=2,
        failed_checks=0,
    )
    assert report.passed
    assert report.total_checks == 2

    # Failed check
    c3 = CheckResult(name="counts", table="orders", passed=False, expected="500", actual="499")
    report_failed = VerifyReport(
        passed=False,
        checks=[c1, c2, c3],
        total_checks=3,
        passed_checks=2,
        failed_checks=1,
    )
    assert not report_failed.passed
