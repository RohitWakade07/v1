import subprocess
import sys
from pathlib import Path
from graders.base_grader import BaseGrader, CheckResult, GradingResult

class Week4Grader(BaseGrader):
    def grade(self) -> GradingResult:
        checks = []
        week_dir = self.workspace
        
        # Helper to run git commands
        def run_git(*args):
            try:
                res = subprocess.run(
                    ["git", *args],
                    cwd=str(week_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return res.returncode == 0, res.stdout, res.stderr
            except Exception as e:
                return False, "", str(e)

        # Check 1: Git Repository Exists
        git_dir = week_dir / ".git"
        git_exists = git_dir.exists() and git_dir.is_dir()
        checks.append(
            CheckResult(
                name="Git Repository Exists",
                passed=git_exists,
                marks=1.0 if git_exists else 0.0,
                max_marks=1.0,
                reason="Found .git directory." if git_exists else "No .git directory found. Did you initialize or clone the repo?",
                hint="Ensure you include the hidden .git folder in your submission zip.",
            )
        )

        if not git_exists:
            return GradingResult(score=0.0, max_score=5.0, passed=False, checks=checks, feedback="Not a git repository.")

        # Check 2: Required Files
        recovery_md = week_dir / "RECOVERY.md"
        gitignore = week_dir / ".gitignore"
        has_recovery = recovery_md.exists() and recovery_md.is_file()
        has_gitignore = gitignore.exists() and gitignore.is_file()
        
        req_passed = has_recovery and has_gitignore
        req_reason = "Found both RECOVERY.md and .gitignore." if req_passed else "Missing RECOVERY.md or .gitignore."
        checks.append(
            CheckResult(
                name="Required Files",
                passed=req_passed,
                marks=1.0 if req_passed else 0.0,
                max_marks=1.0,
                reason=req_reason,
                hint="You must submit a RECOVERY.md file documenting your steps, and a .gitignore file.",
            )
        )

        # Check 3: Ignore Rules & Untracked Binaries/Logs
        ignore_passed = False
        ignore_reason = "Failed to evaluate git tree."
        if has_gitignore:
            success, ls_files, _ = run_git("ls-files")
            if success:
                logs_tracked = any(f.endswith(".log") for f in ls_files.splitlines())
                if logs_tracked:
                    ignore_reason = "Log files are still tracked by Git! You need to remove them from the index (git rm --cached)."
                else:
                    ignore_passed = True
                    ignore_reason = ".log files are successfully untracked/ignored."
        
        checks.append(
            CheckResult(
                name="Cleaned Index & Ignore Rules",
                passed=ignore_passed,
                marks=1.0 if ignore_passed else 0.0,
                max_marks=1.0,
                reason=ignore_reason,
                hint="Make sure .log and large binaries are added to .gitignore AND removed from git's tracking index.",
            )
        )

        # Check 4: Clean Working Tree
        success, status_out, _ = run_git("status", "--porcelain")
        tree_clean = success and len(status_out.strip()) == 0
        checks.append(
            CheckResult(
                name="Clean Working Tree",
                passed=tree_clean,
                marks=1.0 if tree_clean else 0.0,
                max_marks=1.0,
                reason="Working tree is clean." if tree_clean else f"Working tree has uncommitted changes:\n{status_out}",
                hint="Commit all your changes, including RECOVERY.md, before zipping.",
            )
        )

        # Check 5: Git History (Merge & Amend)
        success, log_out, _ = run_git("log", "--oneline")
        commits = log_out.strip().splitlines()
        history_passed = success and len(commits) > 1
        checks.append(
            CheckResult(
                name="Commit History Verified",
                passed=history_passed,
                marks=1.0 if history_passed else 0.0,
                max_marks=1.0,
                reason=f"Found {len(commits)} commits in history." if history_passed else "Git history is too short or missing.",
                hint="Your repository should have a history showing the amended commit and the merge.",
            )
        )

        total_score = sum(c.marks for c in checks)
        total_max = sum(c.max_marks for c in checks)
        score_pct = (total_score / total_max) * 100 if total_max > 0 else 0.0
        passed = score_pct >= 60.0

        return GradingResult(
            score=round(total_score, 2),
            max_score=round(total_max, 2),
            passed=passed,
            checks=checks,
            feedback=f"Completed Git Recovery Challenge checks. Score: {total_score}/{total_max}",
        )
