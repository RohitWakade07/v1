"""
EEP verifier grading — rubric and scoring ported from the legacy Flask grader.
"""

from __future__ import annotations

# Week → prefix → point value
EEP_RUBRICS: dict[str, dict[str, float]] = {
    "1": {
        "dir:week-": 1,
        "dir:notes": 2,
        "dir:scripts": 2,
        "dir:capstone": 2,
        "readme:week-": 1,
        "bashrc": 5,
        "workspace-report": 5,
    },
    "2": {
        "dir:week-02": 5,
        "file:server.log": 5,
        "file:analyze.sh": 10,
        "executable:analyze": 5,
        "script:runs": 10,
        "output:report.txt": 10,
        "analysis:request_count": 10,
        "analysis:top_ips": 10,
        "analysis:top_urls": 10,
        "analysis:status_codes": 10,
        "technique:pipelines": 10,
        "technique:redirection": 5,
    },
    "3": {
        "dir:week-03": 5,
        "file:organize.sh": 10,
        "executable:organize": 5,
        "validation:no_args": 5,
        "validation:bad_dir": 5,
        "org:creates_folders": 10,
        "org:documents_correct": 10,
        "org:images_correct": 10,
        "org:code_correct": 10,
        "org:other_correct": 10,
        "org:no_files_left": 5,
        "org:summary_output": 5,
        "technique:conditionals": 5,
        "technique:loop": 5,
    },
}

EEP_MAX_SCORES: dict[str, float] = {
    "1": 40,
    "2": 100,
    "3": 100,
}

# Optional human-readable labels and hints for checks_detail
EEP_CHECK_META: dict[str, dict[str, tuple[str, str]]] = {
    "1": {
        "dir:week-": ("Weekly folder", "Create the missing week folder under ~/eep-software/"),
        "dir:notes": ("Notes folder", "Run: mkdir ~/eep-software/notes"),
        "dir:scripts": ("Scripts folder", "Run: mkdir ~/eep-software/scripts"),
        "dir:capstone": ("Capstone folder", "Run: mkdir ~/eep-software/capstone"),
        "readme:week-": ("Weekly README", "Add README.md in the week folder"),
        "bashrc": ("Bash aliases", "Add at least 2 aliases to ~/.bashrc"),
        "workspace-report": ("Workspace report", "Generate workspace-report.txt"),
    },
    "2": {
        "dir:week-02": ("Week 2 directory", "Create ~/eep-software/week-02"),
        "file:server.log": ("Sample log file", "Place server.log in week-02"),
        "file:analyze.sh": ("Analysis script", "Create analyze.sh"),
        "executable:analyze": ("Script executable", "chmod +x analyze.sh"),
        "script:runs": ("Script runs OK", "Fix errors so analyze.sh runs"),
        "output:report.txt": ("Produces report.txt", "Script must write report.txt"),
        "analysis:request_count": ("Request count", "Pipeline counting log lines"),
        "analysis:top_ips": ("Top IPs", "Pipeline for top IP addresses"),
        "analysis:top_urls": ("Top URLs", "Pipeline for top URLs"),
        "analysis:status_codes": ("Status codes", "Pipeline for status distribution"),
        "technique:pipelines": ("Uses pipes", "Use | to chain commands"),
        "technique:redirection": ("Uses redirection", "Use > or >> for output"),
    },
    "3": {
        "dir:week-03": ("Week 3 directory", "Create ~/eep-software/week-03"),
        "file:organize.sh": ("Script exists", "Create organize.sh"),
        "executable:organize": ("Script executable", "chmod +x organize.sh"),
        "validation:no_args": ("Validates no args", "Check argument count"),
        "validation:bad_dir": ("Validates bad dir", "Check directory exists"),
        "org:creates_folders": ("Creates sub-folders", "mkdir Documents/Images/Code/Other"),
        "org:documents_correct": ("Documents sorted", "Move document extensions"),
        "org:images_correct": ("Images sorted", "Move image extensions"),
        "org:code_correct": ("Code sorted", "Move code extensions"),
        "org:other_correct": ("Other sorted", "Move remaining files"),
        "org:no_files_left": ("All files moved", "No files left in root"),
        "org:summary_output": ("Prints summary", "Print file counts"),
        "technique:conditionals": ("Uses conditionals", "Use if/elif or case"),
        "technique:loop": ("Uses loops", "Use for or while"),
    },
}


def get_week_from_filename(filename: str) -> str:
    """Return rubric week '1', '2', or '3' from the uploaded filename."""
    if not filename:
        return "1"
    upper = filename.upper()
    lower = filename.lower()
    if "EEP2" in upper or ".eep2" in lower:
        return "2"
    if "EEP3" in upper or ".eep3" in lower:
        return "3"
    return "1"


def _lookup_rubric_points(name: str, week: str) -> tuple[float, str, str]:
    """Match check name against rubric prefixes; return (points, label, hint)."""
    rubric = EEP_RUBRICS.get(week, EEP_RUBRICS["1"])
    meta = EEP_CHECK_META.get(week, {})
    for prefix, points in rubric.items():
        if name.startswith(prefix):
            label, hint = meta.get(prefix, (name, ""))
            if "week-" in prefix and prefix not in ("dir:week-02", "dir:week-03"):
                label = f"{label} ({name})"
            return points, label, hint
    return 0.0, name, ""


def grade_eep_checks(checks: list, week: str) -> dict:
    """Grade parsed EEP checks against the week rubric."""
    total = EEP_MAX_SCORES.get(week, EEP_MAX_SCORES["1"])
    earned = 0.0
    checks_detail: list[dict] = []
    score_breakdown: dict[str, dict] = {}

    for check in checks:
        name = check.get("name", "")
        status = check.get("status", "FAIL")
        points, label, hint = _lookup_rubric_points(name, week)
        passed = status == "PASS"
        score = points if passed else 0.0
        if passed:
            earned += points
        checks_detail.append({
            "name": name,
            "label": label,
            "points": points,
            "passed": passed,
            "hint": hint,
        })
        score_breakdown[name] = {"passed": passed, "score": score}

    earned = min(earned, total)
    score_pct = round((earned / total * 100) if total else 0, 1)
    passed_overall = score_pct >= 60
    if score_pct >= 100:
        grade = "A+"
    elif score_pct >= 90:
        grade = "A"
    elif score_pct >= 80:
        grade = "B"
    elif score_pct >= 70:
        grade = "C"
    elif score_pct >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "earned": earned,
        "total": total,
        "score_pct": score_pct,
        "passed": passed_overall,
        "grade": grade,
        "checks_detail": checks_detail,
        "score_breakdown": score_breakdown,
    }


def map_checks_to_results(checks: list, week: str) -> dict:
    """Map EEP checks to internal proof test-results shape for audit storage."""
    results: dict[str, dict] = {}
    for check in checks:
        name = check.get("name", "")
        status = check.get("status", "FAIL")
        points, _, _ = _lookup_rubric_points(name, week)
        passed = status == "PASS"
        results[name] = {
            "test_id": name,
            "passed": passed,
            "score": points if passed else 0.0,
            "stdout_hash": None,
            "exit_code": 0,
        }
    return results
