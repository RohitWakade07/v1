"""Unit tests for EEP grading service and report parsing."""

import pytest

from app.core.security import parse_eep_report
from app.services.eep_grading_service import (
    EEP_MAX_SCORES,
    get_week_from_filename,
    grade_eep_checks,
    map_checks_to_results,
)


SAMPLE_REPORT = """STUDENT_ID: 22BEC001
TIMESTAMP: 2026-06-04T10:00:00Z
WEEK: 1
dir:week-01: PASS
dir:notes: PASS
bashrc: FAIL
Overall: FAIL
"""


def test_get_week_from_filename():
    assert get_week_from_filename("STUDENT_EEP2_week2.eep2") == "2"
    assert get_week_from_filename("report.EEP3.eep3") == "3"
    assert get_week_from_filename("week1.eep1") == "1"
    assert get_week_from_filename("") == "1"


def test_parse_eep_report():
    parsed = parse_eep_report(SAMPLE_REPORT)
    assert parsed["student_id"] == "22BEC001"
    assert parsed["timestamp"] == "2026-06-04T10:00:00Z"
    assert parsed["week"] == "1"
    assert parsed["overall"] == "FAIL"
    assert len(parsed["checks"]) == 3
    assert parsed["checks"][0] == {"name": "dir:week-01", "status": "PASS"}


def test_grade_eep_checks_week1_partial():
    checks = [
        {"name": "dir:week-01", "status": "PASS"},
        {"name": "dir:notes", "status": "PASS"},
        {"name": "bashrc", "status": "FAIL"},
    ]
    result = grade_eep_checks(checks, "1")
    assert result["earned"] == 3  # 1 + 2
    assert result["total"] == EEP_MAX_SCORES["1"]
    assert result["score_pct"] == pytest.approx(7.5, rel=0.1)
    assert result["passed"] is False
    assert result["grade"] == "F"
    assert "dir:week-01" in result["score_breakdown"]
    assert result["score_breakdown"]["dir:week-01"]["passed"] is True


def test_grade_eep_checks_pass_threshold():
    checks = [{"name": f"dir:week-{i:02d}", "status": "PASS"} for i in range(1, 25)]
    checks += [
        {"name": "dir:notes", "status": "PASS"},
        {"name": "dir:scripts", "status": "PASS"},
        {"name": "dir:capstone", "status": "PASS"},
        {"name": "bashrc", "status": "PASS"},
        {"name": "workspace-report", "status": "PASS"},
    ]
    result = grade_eep_checks(checks, "1")
    assert result["earned"] == 40
    assert result["passed"] is True
    assert result["grade"] == "A+"


def test_map_checks_to_results():
    checks = [{"name": "dir:week-02", "status": "PASS"}]
    mapped = map_checks_to_results(checks, "2")
    assert "dir:week-02" in mapped
    assert mapped["dir:week-02"]["test_id"] == "dir:week-02"
    assert mapped["dir:week-02"]["passed"] is True
    assert mapped["dir:week-02"]["score"] == 5
    assert mapped["dir:week-02"]["stdout_hash"] is None
