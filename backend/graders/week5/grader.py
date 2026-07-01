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
  1. Clones the student's GitHub repo
  2. Checks for merge conflict markers (absence = good)
  3. Verifies main branch is clean and up-to-date
  4. Checks PR review activity via filesystem evidence
  5. Validates teamwork documentation (TEAMWORK.md or similar)
  6. Checks for collaboration evidence (multiple contributors)

Adapted from external: I-M-Sharma/eep1-grader Week 5 logic.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from graders.base_grader import BaseGrader, CheckResult, GradingResult


def _git(args: list[str], cwd: str, timeout: int = 15) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except FileNotFoundError:
        return 1, "", "git not found"


class Week5Grader(BaseGrader):
    """
    Week 5: GitHub Collaboration.
    The submission ZIP must contain a file named 'submission.json' with
    repo_owner, repo_name, pr_number (and optionally github_token).
    """

    def grade(self) -> GradingResult:
        checks: list[CheckResult] = []

        # ── Parse submission.json ──────────────────────────────────────────
        submission_json = self.workspace / "submission.json"
        # Also accept main.py (for Gradescope compatibility)
        if not submission_json.exists():
            submission_json = self.workspace / "main.py"

        if not submission_json.exists():
            fail_check = CheckResult(
                name="Submission Payload",
                passed=False,
                marks=0.0,
                max_marks=5.0,
                reason="No submission.json found in submitted ZIP.",
                hint="Create a submission.json with: repo_owner, repo_name, pr_number",
            )
            return GradingResult(
                score=0.0, max_score=5.0, passed=False,
                checks=[fail_check],
                feedback="No submission.json found. Cannot grade.",
            )

        try:
            payload = json.loads(submission_json.read_text(errors="ignore"))
        except json.JSONDecodeError as e:
            fail_check = CheckResult(
                name="Submission Payload",
                passed=False,
                marks=0.0,
                max_marks=5.0,
                reason=f"submission.json is not valid JSON: {e}",
                hint="Ensure submission.json is a valid JSON object.",
            )
            return GradingResult(
                score=0.0, max_score=5.0, passed=False,
                checks=[fail_check],
                feedback="Invalid JSON in submission.json.",
            )

        repo_owner = payload.get("repo_owner", "").strip()
        repo_name  = payload.get("repo_name",  "").strip()
        pr_number  = payload.get("pr_number",  "")
        token      = payload.get("github_token", "").strip()

        # ── Check 1: Submission payload complete (0.5 mark) ───────────────
        payload_ok = bool(repo_owner and repo_name and pr_number)
        checks.append(CheckResult(
            name="Submission Payload Complete",
            passed=payload_ok,
            marks=0.5 if payload_ok else 0.0,
            max_marks=0.5,
            reason=(
                f"Payload contains repo_owner={repo_owner}, repo_name={repo_name}, pr_number={pr_number}"
                if payload_ok
                else f"Missing fields. Got: {list(payload.keys())}"
            ),
            hint="submission.json must have: repo_owner, repo_name, pr_number",
        ))

        if not payload_ok:
            return GradingResult(
                score=0.5 if payload_ok else 0.0,
                max_score=5.0,
                passed=False,
                checks=checks,
                feedback="Incomplete submission payload.",
            )

        # ── Clone Repository ───────────────────────────────────────────────
        repo_url = f"https://github.com/{repo_owner}/{repo_name}.git"
        if token:
            repo_url = f"https://{token}@github.com/{repo_owner}/{repo_name}.git"

        repo_dir = str(self.workspace / "_cloned_repo")
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        clone_env = os.environ.copy()
        clone_env["GIT_TERMINAL_PROMPT"] = "0"

        try:
            clone_result = subprocess.run(
                ["git", "clone", "--depth=50", repo_url, repo_dir],
                capture_output=True, text=True, timeout=60, env=clone_env,
            )
            clone_ok = clone_result.returncode == 0
        except subprocess.TimeoutExpired:
            clone_ok = False
            clone_result = type("R", (), {"stderr": "Clone timeout (60s)"})()

        checks.append(CheckResult(
            name="Repository Cloned Successfully",
            passed=clone_ok,
            marks=0.5 if clone_ok else 0.0,
            max_marks=0.5,
            reason=(
                f"Cloned {repo_owner}/{repo_name} successfully."
                if clone_ok
                else f"Failed to clone: {clone_result.stderr[:200]}"
            ),
            hint="Ensure the repository is public or provide a valid GitHub token.",
        ))

        if not clone_ok:
            return GradingResult(
                score=0.5 if payload_ok else 0.0,
                max_score=5.0,
                passed=False,
                checks=checks,
                feedback="Could not clone repository.",
            )

        # ── Check 3: No merge conflict markers (0.5 marks) ────────────────
        conflict_files: list[str] = []
        conflict_marker_re = re.compile(r"^(<{7}|>{7}|={7}|\|{7})\s", re.MULTILINE)
        for fpath in Path(repo_dir).rglob("*"):
            if fpath.is_file() and ".git" not in fpath.parts:
                try:
                    text = fpath.read_text(errors="ignore")
                    if conflict_marker_re.search(text):
                        conflict_files.append(fpath.name)
                except Exception:
                    pass

        no_conflicts = len(conflict_files) == 0
        checks.append(CheckResult(
            name="No Merge Conflict Markers",
            passed=no_conflicts,
            marks=0.5 if no_conflicts else 0.0,
            max_marks=0.5,
            reason=(
                "No unresolved merge conflict markers found."
                if no_conflicts
                else f"Conflict markers in: {', '.join(conflict_files[:5])}"
            ),
            hint="Resolve merge conflicts completely and commit the resolution.",
        ))

        # ── Check 4: Main branch commit count ≥ 3 (0.5 marks) ────────────
        rc, log_out, _ = _git(["log", "--oneline", "-20"], repo_dir)
        commits = [l for l in log_out.splitlines() if l.strip()] if rc == 0 else []
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

        # ── Check 5: PR evidence — feature branch merged or present (1.0 mark)
        rc_br, branches_raw, _ = _git(["branch", "-a"], repo_dir)
        branches = [b.strip().lstrip("* ").replace("remotes/origin/", "")
                    for b in branches_raw.splitlines() if b.strip()]
        has_feature_branch = any(
            b.lower() not in {"main", "master", "head"} and "HEAD" not in b
            for b in branches
        )

        # Check for merged branch evidence in git log
        rc_mg, merged_log, _ = _git(
            ["log", "--merges", "--oneline", "-5"], repo_dir
        )
        has_merge_commit = bool(merged_log.strip()) if rc_mg == 0 else False
        pr_evidence = has_feature_branch or has_merge_commit

        checks.append(CheckResult(
            name="PR / Feature Branch Evidence",
            passed=pr_evidence,
            marks=1.0 if pr_evidence else 0.0,
            max_marks=1.0,
            reason=(
                f"Feature branch found: {[b for b in branches if b not in ('main','master')][0]}"
                if has_feature_branch else
                "Merge commit found in history." if has_merge_commit else
                "No feature branch or merge commits found."
            ),
            hint=(
                "Create a feature branch and raise a PR. "
                "Evidence should be visible in the repository's branch list or merge history."
            ),
        ))

        # ── Check 6: TEAMWORK.md / collaboration doc (1.0 mark) ───────────
        teamwork_files = [
            "TEAMWORK.md", "teamwork.md", "COLLABORATION.md",
            "collaboration.md", "CONTRIBUTING.md",
        ]
        teamwork_path = None
        for fname in teamwork_files:
            candidate = Path(repo_dir) / fname
            if candidate.is_file():
                teamwork_path = candidate
                break

        has_teamwork_doc = teamwork_path is not None
        teamwork_content_ok = False
        if has_teamwork_doc:
            content = teamwork_path.read_text(errors="ignore")
            word_count = len(content.split())
            teamwork_content_ok = word_count >= 30

        checks.append(CheckResult(
            name="Teamwork Documentation (TEAMWORK.md)",
            passed=teamwork_content_ok,
            marks=1.0 if teamwork_content_ok else (0.5 if has_teamwork_doc else 0.0),
            max_marks=1.0,
            reason=(
                f"{teamwork_path.name} found with {len(teamwork_path.read_text().split())} words."
                if has_teamwork_doc
                else "No TEAMWORK.md or COLLABORATION.md found."
            ),
            hint="Create TEAMWORK.md describing how your team collaborated, divided work, and resolved issues.",
        ))

        # ── Check 7: Multiple contributors evidence (0.5 marks) ──────────
        rc_auth, authors_out, _ = _git(
            ["log", "--format=%ae", "--all"], repo_dir
        )
        unique_authors: set[str] = set()
        if rc_auth == 0:
            unique_authors = {a.strip() for a in authors_out.splitlines() if a.strip()}
        multiple_contributors = len(unique_authors) >= 2

        checks.append(CheckResult(
            name=f"Multiple Contributors ({len(unique_authors)} found)",
            passed=multiple_contributors,
            marks=1.0 if multiple_contributors else 0.0,
            max_marks=1.0,
            reason=(
                f"Found {len(unique_authors)} unique contributor(s): {', '.join(list(unique_authors)[:3])}"
            ),
            hint=(
                "Ensure all team members commit directly to the shared repository, "
                "not just one person pushing everyone's code."
            ),
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
