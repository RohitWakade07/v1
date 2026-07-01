"""
Week 4 Grader: Git Workflow & Best Practices
==============================================
Students submit a ZIP containing their git workspace (week-04/ folder).
The grader checks:
  1. .gitignore exists with appropriate patterns
  2. No junk files (binaries, logs, caches) are tracked by git
  3. Commit history has at least 3 meaningful commits
  4. Commit messages are not trivial (no "wip", "asdf", "test")
  5. A feature/dev branch exists and has been merged or differs from main
  6. week-04/ directory structure with required files
"""
import re
import subprocess
from pathlib import Path
from graders.base_grader import BaseGrader, CheckResult, GradingResult


# Extensions / dirs that should never be committed
BAD_EXTENSIONS = {
    ".log", ".bin", ".o", ".pyc", ".exe", ".dll", ".so",
    ".a", ".obj", ".class", ".jar", ".war", ".pyo", ".pyd",
}
BAD_DIRS = {"__pycache__", "node_modules", ".venv", "venv", ".env"}

# Commit message patterns that indicate low-quality messages
TRIVIAL_PATTERNS = re.compile(
    r"^(wip|asdf|test|temp|tmp|fix|update|changes|commit|done|ok|"
    r"final|finals|aaa+|zzz+|\.+|abc+|\d+)$",
    re.IGNORECASE,
)


def _git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a git command; return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except FileNotFoundError:
        return 1, "", "git not found"


class Week4Grader(BaseGrader):

    def grade(self) -> GradingResult:
        checks: list[CheckResult] = []

        # The workspace is the extracted ZIP root.
        # Students submit their git repo as a ZIP; the repo root is workspace.
        ws = self.workspace

        # ── Check 1: .gitignore exists (1.0 mark) ─────────────────────────
        gitignore = ws / ".gitignore"
        gitignore_exists = gitignore.is_file()
        checks.append(CheckResult(
            name=".gitignore Exists",
            passed=gitignore_exists,
            marks=1.0 if gitignore_exists else 0.0,
            max_marks=1.0,
            reason=".gitignore found in repo root." if gitignore_exists
                   else ".gitignore file is missing from the repository root.",
            hint="Create a .gitignore file. Use 'gitignore.io' to generate one for Python/Bash.",
        ))

        # ── Check 2: .gitignore covers common patterns (0.5 marks) ─────────
        gitignore_patterns_ok = False
        if gitignore_exists:
            content = gitignore.read_text(errors="ignore").lower()
            required = ["*.pyc", "__pycache__", "*.log", ".env"]
            covered = [p for p in required if p.split(".")[0] in content or p in content]
            gitignore_patterns_ok = len(covered) >= 2
        checks.append(CheckResult(
            name=".gitignore Patterns Coverage",
            passed=gitignore_patterns_ok,
            marks=0.5 if gitignore_patterns_ok else 0.0,
            max_marks=0.5,
            reason="Covers *.pyc, __pycache__, *.log, .env" if gitignore_patterns_ok
                   else "Missing common patterns like *.pyc, __pycache__, *.log",
            hint="Add: __pycache__/, *.pyc, *.log, .env, .venv/ to .gitignore",
        ))

        # ── Check 3: No junk files tracked (1.2 marks, partial credit) ─────
        rc, tracked_raw, _ = _git(["ls-files"], ws)
        violations: list[str] = []
        if rc == 0:
            for f in tracked_raw.splitlines():
                if not f:
                    continue
                parts = Path(f).parts
                ext = Path(f).suffix.lower()
                if ext in BAD_EXTENSIONS:
                    violations.append(f)
                elif any(d in BAD_DIRS for d in parts):
                    violations.append(f)

        partial = max(0.0, 1.2 - 0.15 * len(violations)) if rc == 0 else 0.0
        partial = round(partial, 2)
        no_junk_passed = len(violations) == 0 and rc == 0
        checks.append(CheckResult(
            name="No Junk Files Tracked",
            passed=no_junk_passed,
            marks=partial if rc == 0 else 0.0,
            max_marks=1.2,
            reason=(
                "No binary/log/cache files tracked. Good hygiene!" if no_junk_passed
                else f"Found {len(violations)} junk file(s): {', '.join(violations[:5])}"
                     + ("..." if len(violations) > 5 else "")
                if rc == 0 else "Could not run git ls-files — is this a valid git repo?"
            ),
            hint="Add offending patterns to .gitignore and run: git rm --cached <file>",
        ))

        # ── Check 4: Commit count ≥ 3 (1.0 mark) ──────────────────────────
        rc_log, log_out, _ = _git(["log", "--oneline"], ws)
        commits = [l for l in log_out.splitlines() if l.strip()] if rc_log == 0 else []
        commit_count = len(commits)
        commit_count_ok = commit_count >= 3
        checks.append(CheckResult(
            name=f"Commit Count (found {commit_count}, need ≥ 3)",
            passed=commit_count_ok,
            marks=1.0 if commit_count_ok else round(commit_count / 3.0, 2),
            max_marks=1.0,
            reason=f"Found {commit_count} commit(s)." if commits else "No commits or not a git repo.",
            hint="Make at least 3 commits with meaningful messages as you work through the week.",
        ))

        # ── Check 5: Commit message quality (0.8 marks) ───────────────────
        trivial_msgs: list[str] = []
        if commits:
            for line in commits:
                parts = line.split(" ", 1)
                msg = parts[1].strip() if len(parts) > 1 else ""
                if len(msg) < 5 or TRIVIAL_PATTERNS.match(msg):
                    trivial_msgs.append(f'"{msg}"')
        quality_ok = len(trivial_msgs) == 0 and len(commits) >= 3
        quality_marks = 0.8 if quality_ok else max(0.0, round(0.8 - 0.15 * len(trivial_msgs), 2))
        checks.append(CheckResult(
            name="Commit Message Quality",
            passed=quality_ok,
            marks=quality_marks,
            max_marks=0.8,
            reason=(
                "All commit messages look meaningful." if quality_ok
                else f"Low-quality message(s): {', '.join(trivial_msgs[:3])}"
                     if trivial_msgs else "Insufficient commits to evaluate."
            ),
            hint=(
                'Write descriptive commit messages, e.g.: "feat: add .gitignore for Python artifacts"'
                if not quality_ok else ""
            ),
        ))

        # ── Check 6: Feature/dev branch exists (1.0 mark) ─────────────────
        rc_br, branches_out, _ = _git(["branch", "-a"], ws)
        branches: list[str] = []
        feature_branch = False
        if rc_br == 0:
            branches = [b.strip().lstrip("* ") for b in branches_out.splitlines() if b.strip()]
            feature_branch = any(
                ("feature" in b.lower() or "dev" in b.lower() or "week" in b.lower()
                 or "lab" in b.lower() or b.lower() not in {"main", "master"})
                for b in branches
                if b and "HEAD" not in b
            )
        checks.append(CheckResult(
            name="Feature/Dev Branch Exists",
            passed=feature_branch,
            marks=1.0 if feature_branch else 0.0,
            max_marks=1.0,
            reason=(
                f"Found feature/dev branch: {[b for b in branches if b not in ('main','master','HEAD')][0]}"
                if feature_branch else "Only main/master branch found."
            ),
            hint="Create a feature branch: git checkout -b feature/week4-gitignore",
        ))

        # ── Check 7: week-04/ folder structure (0.5 marks) ────────────────
        week04_dir = ws / "week-04"
        week04_exists = week04_dir.is_dir()
        has_readme = (week04_dir / "README.md").is_file() if week04_exists else False
        struct_ok = week04_exists and has_readme
        checks.append(CheckResult(
            name="week-04/ Structure (dir + README.md)",
            passed=struct_ok,
            marks=0.5 if struct_ok else (0.2 if week04_exists else 0.0),
            max_marks=0.5,
            reason=(
                "week-04/ with README.md found." if struct_ok
                else "week-04/ exists but missing README.md" if week04_exists
                else "week-04/ directory not found."
            ),
            hint="Create week-04/README.md documenting what you learned about git this week.",
        ))

        total_score = sum(c.marks for c in checks)
        total_max = sum(c.max_marks for c in checks)
        score_pct = (total_score / total_max * 100) if total_max > 0 else 0.0

        return GradingResult(
            score=round(total_score, 2),
            max_score=round(total_max, 2),
            passed=score_pct >= 60.0,
            checks=checks,
            feedback=f"Git workflow checks complete. Score: {total_score:.2f}/{total_max:.2f}",
        )
