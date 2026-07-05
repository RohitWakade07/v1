import json
from graders.base_grader import BaseGrader, CheckResult, GradingResult

class Week5Grader(BaseGrader):
    def grade(self) -> GradingResult:
        checks: list[CheckResult] = []

        submission_json = self.workspace / "submission.json"
        if not submission_json.exists():
            submission_json = self.workspace / "main.py"

        if not submission_json.exists():
            fail_check = CheckResult(
                name="Submission Payload",
                passed=False, marks=0.0, max_marks=5.0,
                reason="No submission.json found in submitted ZIP.",
                hint="Create a submission.json with: repo_owner, repo_name, pr_number",
            )
            return GradingResult(score=0.0, max_score=5.0, passed=False, checks=[fail_check], feedback="No submission.json found. Cannot grade.")

        try:
            payload = json.loads(submission_json.read_text(errors="ignore"))
        except Exception as e:
            fail_check = CheckResult(
                name="Submission Payload", passed=False, marks=0.0, max_marks=5.0,
                reason=f"submission.json is not valid JSON.",
                hint="Ensure submission.json is a valid JSON object.",
            )
            return GradingResult(score=0.0, max_score=5.0, passed=False, checks=[fail_check], feedback="Invalid JSON in submission.json.")

        repo_owner = payload.get("repo_owner", "").strip()
        repo_name  = payload.get("repo_name",  "").strip()
        pr_number  = payload.get("pr_number",  "")

        # ── Check 1: Submission payload complete (0.5 mark) ───────────────
        payload_ok = bool(repo_owner and repo_name and pr_number)
        checks.append(CheckResult(
            name="Submission Payload Complete",
            passed=payload_ok,
            marks=0.5 if payload_ok else 0.0,
            max_marks=0.5,
            reason=(f"Payload contains repo_owner={repo_owner}, repo_name={repo_name}, pr_number={pr_number}" if payload_ok else f"Missing fields."),
            hint="submission.json must have: repo_owner, repo_name, pr_number",
        ))

        if not payload_ok:
            return GradingResult(score=0.5 if payload_ok else 0.0, max_score=5.0, passed=False, checks=checks, feedback="Incomplete submission payload.")

        # Read result from wrapper
        result_json_path = self.workspace / "result.json"
        if not result_json_path.exists():
            fail_check = CheckResult(
                name="Grader Execution", passed=False, marks=0.0, max_marks=4.5,
                reason="Grader did not produce a result.json (possible timeout or crash).",
                hint="Contact support if this persists.",
            )
            checks.append(fail_check)
            return GradingResult(score=0.5, max_score=5.0, passed=False, checks=checks, feedback="Grader crashed.")

        try:
            result = json.loads(result_json_path.read_text(errors="ignore"))
        except Exception:
            return GradingResult(score=0.5, max_score=5.0, passed=False, checks=checks, feedback="Invalid result.json from wrapper.")

        if "error" in result:
            checks.append(CheckResult(
                name="Wrapper Error", passed=False, marks=0.0, max_marks=4.5,
                reason=result["error"], hint="Fix wrapper errors."
            ))
            return GradingResult(score=0.5, max_score=5.0, passed=False, checks=checks, feedback="Wrapper error.")

        clone_ok = result.get("clone_ok", False)
        clone_error = result.get("clone_error", "")
        checks.append(CheckResult(
            name="Repository Cloned Successfully",
            passed=clone_ok,
            marks=0.5 if clone_ok else 0.0,
            max_marks=0.5,
            reason=f"Cloned {repo_owner}/{repo_name} successfully." if clone_ok else f"Failed to clone: {clone_error}",
            hint="Ensure the repository is public or provide a valid GitHub token.",
        ))

        if not clone_ok:
            return GradingResult(score=1.0 if payload_ok and clone_ok else 0.5, max_score=5.0, passed=False, checks=checks, feedback="Could not clone repository.")

        # Specific check: integration-fix branch exists or merged
        branches = result.get("branches", [])
        merged_log = result.get("merged_log", "")
        has_integration_fix = any("integration-fix" in b for b in branches) or "integration-fix" in merged_log
        checks.append(CheckResult(
            name="Integration Fix Branch",
            passed=has_integration_fix,
            marks=0.5 if has_integration_fix else 0.0,
            max_marks=0.5,
            reason="Found 'integration-fix' branch or merge commit." if has_integration_fix else "No 'integration-fix' branch found.",
            hint="Create a branch named 'integration-fix' for resolving conflicts.",
        ))

        # Check: No merge conflict markers
        conflict_files = result.get("conflict_files", [])
        no_conflicts = len(conflict_files) == 0
        checks.append(CheckResult(
            name="No Merge Conflict Markers",
            passed=no_conflicts,
            marks=0.5 if no_conflicts else 0.0,
            max_marks=0.5,
            reason="No unresolved merge conflict markers found." if no_conflicts else f"Conflict markers in: {', '.join(conflict_files[:5])}",
            hint="Resolve merge conflicts completely and commit the resolution.",
        ))
        
        # Check: Pytest passed
        tests_passed = result.get("tests_passed", False)
        checks.append(CheckResult(
            name="Unit Tests Passing",
            passed=tests_passed,
            marks=1.0 if tests_passed else 0.0,
            max_marks=1.0,
            reason="pytest executed successfully and all tests passed." if tests_passed else "Unit tests failed. See GitHub Actions or run pytest locally.",
            hint="Fix the broken test in tests/test_controller.py and any edge case bugs.",
        ))
        
        # Check: Dynamic Configuration (os.environ in config.py)
        config_py = result.get("config_py", "")
        has_env = "os.environ" in config_py or "getenv" in config_py
        checks.append(CheckResult(
            name="Dynamic Configuration (MAX_SPEED)",
            passed=has_env,
            marks=0.5 if has_env else 0.0,
            max_marks=0.5,
            reason="Found os.environ or getenv in config.py." if has_env else "Did not find os.environ or getenv in config.py.",
            hint="Address the code review comment by making MAX_SPEED configurable via os.environ.",
        ))
        
        # Check: Sensors Docstring
        sensors_py = result.get("sensors_py", "")
        # very basic check to see if there's a docstring in calibrate
        has_docstring = '\"\"\"' in sensors_py or '\'\'\'' in sensors_py
        checks.append(CheckResult(
            name="Sensor Calibration Docstring",
            passed=has_docstring,
            marks=0.5 if has_docstring else 0.0,
            max_marks=0.5,
            reason="Found docstring in sensors.py." if has_docstring else "Missing docstring in sensors.py.",
            hint="Add a docstring to the calibrate function in sensors.py as requested in review comments.",
        ))

        # Teamwork Check
        teamwork_path = result.get("teamwork_path")
        teamwork_words = result.get("teamwork_words", 0)
        has_teamwork_doc = teamwork_path is not None
        teamwork_content_ok = teamwork_words >= 30
        checks.append(CheckResult(
            name="Teamwork Documentation",
            passed=teamwork_content_ok,
            marks=0.5 if teamwork_content_ok else (0.2 if has_teamwork_doc else 0.0),
            max_marks=0.5,
            reason=(
                f"{teamwork_path} found with {teamwork_words} words."
                if has_teamwork_doc
                else "No TEAMWORK.md or COLLABORATION.md found."
            ),
            hint="Create TEAMWORK.md describing how your team collaborated, divided work, and resolved issues.",
        ))

        # Contributors Check
        contributors = result.get("contributors", [])
        multiple_contributors = len(contributors) >= 2
        checks.append(CheckResult(
            name="Multiple Contributors",
            passed=multiple_contributors,
            marks=0.5 if multiple_contributors else 0.0,
            max_marks=0.5,
            reason=f"Found {len(contributors)} unique contributor(s).",
            hint="Ensure all team members commit directly to the shared repository.",
        ))

        total_score = sum(c.marks for c in checks)
        total_max   = sum(c.max_marks for c in checks)
        score_pct   = (total_score / total_max * 100) if total_max > 0 else 0.0

        return GradingResult(
            score=round(total_score, 2),
            max_score=round(total_max, 2),
            passed=score_pct >= 60.0,
            checks=checks,
            feedback=f"GitHub collaboration checks complete. Score: {total_score:.2f}/{total_max:.2f}",
        )
