"""
Week 5 Grader: GitHub Collaboration & Pull Requests
=====================================================
Students submit a JSON payload (submitted as their "file") containing:
  {
    "repo_owner": "their-github-username",
    "repo_name":  "their-repo-name",
    "pr_number":  123,
    "github_token": "ghp_xxx"   # optional but needed for private repos
  }

The grader:
  1. Clones the student's GitHub repo (via test_wrapper.py inside Docker)
  2. Checks for merge conflict markers (absence = good)
  3. Verifies main branch is clean and up-to-date
  4. Checks PR review activity via filesystem evidence
  5. Validates teamwork documentation (TEAMWORK.md or similar)
  6. Checks for collaboration evidence (multiple contributors)
"""
import json
from graders.base_grader import BaseGrader, CheckResult, GradingResult


class Week5Grader(BaseGrader):
    """
    Week 5: GitHub Collaboration.
    """

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

        commits = result.get("commits", [])
        commit_count = len(commits)
        main_commits_ok = commit_count >= 3
        checks.append(CheckResult(
            name=f"Commit History (found {commit_count}, need ≥ 3)",
            passed=main_commits_ok,
            marks=0.5 if main_commits_ok else round(commit_count / 6.0, 2),
            max_marks=0.5,
            reason=f"{commit_count} commit(s) found in main branch.",
            hint="Ensure the main branch has at least 3 commits showing incremental work.",
        ))

        branches = result.get("branches", [])
        has_feature_branch = any(
            b.lower() not in {"main", "master", "head"} and "head" not in b.lower()
            for b in branches
        )
        merged_log = result.get("merged_log", "")
        has_merge_commit = bool(merged_log)
        pr_evidence = has_feature_branch or has_merge_commit
        
        feature_branch_name = [b for b in branches if b.lower() not in ('main','master','head') and "head" not in b.lower()]
        feature_branch_name = feature_branch_name[0] if feature_branch_name else ""

        checks.append(CheckResult(
            name="PR / Feature Branch Evidence",
            passed=pr_evidence,
            marks=1.0 if pr_evidence else 0.0,
            max_marks=1.0,
            reason=(
                f"Feature branch found: {feature_branch_name}"
                if has_feature_branch else
                "Merge commit found in history." if has_merge_commit else
                "No feature branch or merge commits found."
            ),
            hint=(
                "Create a feature branch and raise a PR. "
                "Evidence should be visible in the repository's branch list or merge history."
            ),
        ))

        teamwork_path = result.get("teamwork_path")
        teamwork_words = result.get("teamwork_words", 0)
        has_teamwork_doc = teamwork_path is not None
        teamwork_content_ok = teamwork_words >= 30
        checks.append(CheckResult(
            name="Teamwork Documentation (TEAMWORK.md)",
            passed=teamwork_content_ok,
            marks=1.0 if teamwork_content_ok else (0.5 if has_teamwork_doc else 0.0),
            max_marks=1.0,
            reason=(
                f"{teamwork_path} found with {teamwork_words} words."
                if has_teamwork_doc
                else "No TEAMWORK.md or COLLABORATION.md found."
            ),
            hint="Create TEAMWORK.md describing how your team collaborated, divided work, and resolved issues.",
        ))

        contributors = result.get("contributors", [])
        multiple_contributors = len(contributors) >= 2
        checks.append(CheckResult(
            name=f"Multiple Contributors ({len(contributors)} found)",
            passed=multiple_contributors,
            marks=1.0 if multiple_contributors else 0.0,
            max_marks=1.0,
            reason=f"Found {len(contributors)} unique contributor(s): {', '.join(contributors[:3])}",
            hint="Ensure all team members commit directly to the shared repository, not just one person pushing everyone's code.",
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
