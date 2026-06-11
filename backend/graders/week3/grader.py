"""
Week 3 Grader: Automated File Organizer
=========================================
Test harness approach:
  1. A known set of 15 files is injected into week-03/test_mixed/ as an asset.
  2. The student's organize.sh is run: `bash organize.sh test_mixed`
  3. We verify each file landed in the EXACT expected destination subfolder.

Known fixture files in test_mixed/:
  Documents/ ← a.txt, b.txt, c.txt, d.txt, e.pdf, f.pdf
  Images/    ← g.jpg, h.jpg, i.jpg, j.png, k.png
  Code/      ← l.py, m.py, n.sh
  Other/     ← o.csv
"""
import subprocess
from pathlib import Path
from graders.base_grader import BaseGrader, CheckResult, GradingResult


# Exact file-to-folder mapping that organize.sh must produce
EXPECTED_PLACEMENT: dict[str, str] = {
    "a.txt": "Documents",
    "b.txt": "Documents",
    "c.txt": "Documents",
    "d.txt": "Documents",
    "e.pdf": "Documents",
    "f.pdf": "Documents",
    "g.jpg": "Images",
    "h.jpg": "Images",
    "i.jpg": "Images",
    "j.png": "Images",
    "k.png": "Images",
    "l.py":  "Code",
    "m.py":  "Code",
    "n.sh":  "Code",
    "o.csv": "Other",
}


class Week3Grader(BaseGrader):
    def grade(self) -> GradingResult:
        checks = []
        exec_res = self.config.get("execution_result", {})
        exit_code = exec_res.get("exit_code")
        timed_out = exec_res.get("timed_out", False)
        oom_killed = exec_res.get("oom_killed", False)
        stdout = exec_res.get("stdout", "")

        week_dir = self.workspace
        test_mixed = week_dir / "test_mixed"

        # ── Check 1: Script ran successfully ──────────────────────────────
        exit_passed = (exit_code == 0 and not timed_out and not oom_killed)
        if timed_out:
            exit_reason = "Script timed out."
        elif oom_killed:
            exit_reason = "Script ran out of memory."
        elif exit_code is not None and exit_code != 0:
            exit_reason = f"Script exited with non-zero code: {exit_code}."
        elif exit_code is None:
            exit_reason = "Script was not executed or crashed."
        else:
            exit_reason = "Script ran successfully."

        checks.append(CheckResult(
            name="Script Exit Status",
            passed=exit_passed,
            marks=0.5 if exit_passed else 0.0,
            max_marks=0.5,
            reason=exit_reason,
            hint="Ensure organize.sh runs without errors when given a valid directory.",
        ))

        # ── Check 2-16: Each file is in the correct destination folder ─────
        correct_placements = 0
        wrong_placements = []
        for filename, expected_folder in EXPECTED_PLACEMENT.items():
            correct_path = test_mixed / expected_folder / filename
            placed_correctly = correct_path.exists() and correct_path.is_file()
            if placed_correctly:
                correct_placements += 1
            else:
                # Also check if still in root (not moved at all)
                in_root = (test_mixed / filename).exists()
                wrong_placements.append(
                    f"{filename} → expected {expected_folder}/ "
                    + ("(still in root)" if in_root else "(missing)")
                )

        # Score: 3.0 marks total, scaled by fraction of correct placements
        placement_marks = round((correct_placements / len(EXPECTED_PLACEMENT)) * 3.0, 2)
        placement_passed = correct_placements == len(EXPECTED_PLACEMENT)
        checks.append(CheckResult(
            name=f"File Placement (correct: {correct_placements}/{len(EXPECTED_PLACEMENT)})",
            passed=placement_passed,
            marks=placement_marks,
            max_marks=3.0,
            reason="All files correctly placed." if placement_passed
                   else f"Incorrect: {'; '.join(wrong_placements[:5])}{'...' if len(wrong_placements) > 5 else ''}",
            hint="Move .txt/.pdf → Documents/, .jpg/.png → Images/, .py/.sh → Code/, .csv → Other/",
        ))

        # ── Check 3: No files remain in test_mixed/ root ──────────────────
        if test_mixed.exists():
            root_files = [p.name for p in test_mixed.iterdir() if p.is_file()]
        else:
            root_files = []
        root_cleared = len(root_files) == 0
        checks.append(CheckResult(
            name="Root Directory Cleared",
            passed=root_cleared,
            marks=0.3 if root_cleared else 0.0,
            max_marks=0.3,
            reason="No files left in test_mixed/ root." if root_cleared
                   else f"Files still in root: {', '.join(root_files)}",
            hint="Every file in test_mixed/ must be moved to a subfolder.",
        ))

        # ── Check 4: stdout contains a numeric summary ────────────────────
        has_numbers = any(c.isdigit() for c in stdout)
        checks.append(CheckResult(
            name="Summary Printed to stdout",
            passed=has_numbers,
            marks=0.2 if has_numbers else 0.0,
            max_marks=0.2,
            reason="Numeric summary found in stdout." if has_numbers else "No numbers in stdout.",
            hint="Print how many files were moved, e.g. 'Documents: 6 files'.",
        ))

        # ── Check 5 & 6: Error handling (no args / non-existent dir) ──────
        organize_sh = week_dir / "organize.sh"
        no_args_passed, nonexistent_passed = False, False
        no_args_reason, nonexistent_reason = "Script not found.", "Script not found."

        if organize_sh.exists():
            try:
                r = subprocess.run(
                    ["bash", "organize.sh"],
                    cwd=str(week_dir), capture_output=True, text=True, timeout=5,
                )
                if r.returncode != 0:
                    no_args_passed = True
                    no_args_reason = f"Correctly rejected empty call (exit {r.returncode})."
                else:
                    no_args_reason = "Script exited 0 when called with no arguments (should fail)."
            except Exception as e:
                no_args_reason = f"Error: {e}"

            try:
                r2 = subprocess.run(
                    ["bash", "organize.sh", "/totally_nonexistent_dir_xyz"],
                    cwd=str(week_dir), capture_output=True, text=True, timeout=5,
                )
                if r2.returncode != 0:
                    nonexistent_passed = True
                    nonexistent_reason = f"Correctly rejected non-existent dir (exit {r2.returncode})."
                else:
                    nonexistent_reason = "Script exited 0 for non-existent directory (should fail)."
            except Exception as e:
                nonexistent_reason = f"Error: {e}"

        checks.append(CheckResult(
            name="Error Handling: No Arguments",
            passed=no_args_passed,
            marks=0.5 if no_args_passed else 0.0,
            max_marks=0.5,
            reason=no_args_reason,
            hint="Exit non-zero if no directory argument is provided.",
        ))
        checks.append(CheckResult(
            name="Error Handling: Non-existent Directory",
            passed=nonexistent_passed,
            marks=0.5 if nonexistent_passed else 0.0,
            max_marks=0.5,
            reason=nonexistent_reason,
            hint="Exit non-zero if the target directory does not exist.",
        ))

        total_score = sum(c.marks for c in checks)
        total_max = sum(c.max_marks for c in checks)
        score_pct = (total_score / total_max) * 100 if total_max > 0 else 0.0
        passed = score_pct >= 60.0

        return GradingResult(
            score=round(total_score, 2),
            max_score=round(total_max, 2),
            passed=passed,
            checks=checks,
            feedback=f"File organizer checks complete. Score: {total_score:.2f}/{total_max:.2f}",
        )
