import re
import subprocess
from pathlib import Path
from graders.base_grader import BaseGrader, CheckResult, GradingResult


class Week3Grader(BaseGrader):
    def grade(self) -> GradingResult:
        checks = []

        # Get execution results from first run (from config)
        exec_res = self.config.get("execution_result", {})
        exit_code = exec_res.get("exit_code")
        timed_out = exec_res.get("timed_out", False)
        oom_killed = exec_res.get("oom_killed", False)
        stdout = exec_res.get("stdout", "")

        # Target directories
        week_dir = self.workspace / "week-03"
        test_mixed = week_dir / "test_mixed"

        # Check 1: exit code 0 (0.5 marks)
        exit_passed = (exit_code == 0 and not timed_out and not oom_killed)
        exit_marks = 0.5 if exit_passed else 0.0
        exit_reason = "First run exited successfully."
        if timed_out:
            exit_reason = "Script execution timed out."
        elif oom_killed:
            exit_reason = "Script execution ran out of memory (OOM)."
        elif exit_code is not None and exit_code != 0:
            exit_reason = f"Script exited with non-zero exit code: {exit_code}."

        checks.append(
            CheckResult(
                name="Script Successful Run Check",
                passed=exit_passed,
                marks=exit_marks,
                max_marks=0.5,
                reason=exit_reason,
                hint="Ensure that organize.sh exits with code 0 when given a valid directory.",
            )
        )

        # Check subfolders existence (0.3 marks each)
        subfolders = ["Documents", "Images", "Code", "Other"]
        folder_status = {}
        for folder in subfolders:
            folder_path = test_mixed / folder
            exists = folder_path.exists() and folder_path.is_dir()
            folder_status[folder] = exists
            checks.append(
                CheckResult(
                    name=f"Subfolder {folder} Creation Check",
                    passed=exists,
                    marks=0.3 if exists else 0.0,
                    max_marks=0.3,
                    reason=f"{folder}/ folder exists." if exists else f"{folder}/ folder was not created.",
                    hint=f"Ensure organize.sh creates a '{folder}' directory inside the target directory.",
                )
            )

        # Helper function to count files and check extensions (case-insensitive)
        def inspect_folder(folder_name: str, allowed_exts: dict[str, int]) -> tuple[bool, str]:
            folder_path = test_mixed / folder_name
            if not folder_path.exists() or not folder_path.is_dir():
                return False, f"Folder {folder_name} does not exist."

            files = [p for p in folder_path.iterdir() if p.is_file()]
            ext_counts = {}
            for f in files:
                ext = f.suffix.lower().lstrip(".")
                ext_counts[ext] = ext_counts.get(ext, 0) + 1

            # Check that counts match allowed exts exactly
            match = True
            details = []
            for ext, expected in allowed_exts.items():
                actual = ext_counts.get(ext, 0)
                details.append(f"{actual} {ext}")
                if actual != expected:
                    match = False

            # Check if there are other unexpected file types
            for ext in ext_counts:
                if ext not in allowed_exts:
                    match = False
                    details.append(f"{ext_counts[ext]} unexpected {ext} file(s)")

            reason = f"Found: {', '.join(details)}."
            return match, reason

        # Check 6: Documents contains exactly 6 files — 4 txt + 2 pdf (0.5 marks)
        doc_match, doc_reason = inspect_folder("Documents", {"txt": 4, "pdf": 2})
        checks.append(
            CheckResult(
                name="Documents Folder Contents Check",
                passed=doc_match,
                marks=0.5 if doc_match else 0.0,
                max_marks=0.5,
                reason=doc_reason,
                hint="Documents/ should contain exactly 4 .txt files and 2 .pdf files.",
            )
        )

        # Check 7: Images contains exactly 5 files — 3 jpg + 2 png (0.5 marks)
        img_match, img_reason = inspect_folder("Images", {"jpg": 3, "png": 2})
        checks.append(
            CheckResult(
                name="Images Folder Contents Check",
                passed=img_match,
                marks=0.5 if img_match else 0.0,
                max_marks=0.5,
                reason=img_reason,
                hint="Images/ should contain exactly 3 .jpg files and 2 .png files.",
            )
        )

        # Check 8: Code contains exactly 3 files — 2 py + 1 sh (0.5 marks)
        code_match, code_reason = inspect_folder("Code", {"py": 2, "sh": 1})
        checks.append(
            CheckResult(
                name="Code Folder Contents Check",
                passed=code_match,
                marks=0.5 if code_match else 0.0,
                max_marks=0.5,
                reason=code_reason,
                hint="Code/ should contain exactly 2 .py files and 1 .sh script.",
            )
        )

        # Check 9: Other contains exactly 1 file — csv (0.3 marks)
        other_match, other_reason = inspect_folder("Other", {"csv": 1})
        checks.append(
            CheckResult(
                name="Other Folder Contents Check",
                passed=other_match,
                marks=0.3 if other_match else 0.0,
                max_marks=0.3,
                reason=other_reason,
                hint="Other/ should contain exactly 1 .csv file.",
            )
        )

        # Check 10: no files remain in test_mixed/ root (0.3 marks)
        root_files = []
        if test_mixed.exists() and test_mixed.is_dir():
            root_files = [p for p in test_mixed.iterdir() if p.is_file()]
        root_passed = len(root_files) == 0
        checks.append(
            CheckResult(
                name="Root Directory Cleared Check",
                passed=root_passed,
                marks=0.3 if root_passed else 0.0,
                max_marks=0.3,
                reason=f"No files left in root." if root_passed else f"Found {len(root_files)} files remaining in root.",
                hint="All files inside test_mixed/ must be moved to their respective subfolders.",
            )
        )

        # Check 11: stdout contains at least one number (0.2 marks)
        num_pattern = re.compile(r"\d+")
        stdout_passed = bool(num_pattern.search(stdout))
        checks.append(
            CheckResult(
                name="Stdout Print Summary Check",
                passed=stdout_passed,
                marks=0.2 if stdout_passed else 0.0,
                max_marks=0.2,
                reason="Stdout printed numeric summary." if stdout_passed else "No numbers found in stdout.",
                hint="Ensure that your script prints a summary of how many files were moved (e.g. 'Documents: 6 files').",
            )
        )

        # Negative test cases: run organize.sh with bad inputs
        # NOTE: These subprocess calls run inside the worker container (not bare
        # metal host). The submission workspace is volume-mounted. A future
        # hardening sprint should move these into mini sandbox containers too.
        # TODO(sprint-hardening): Run negative tests inside sandbox container.
        organize_sh = week_dir / "organize.sh"
        no_args_passed = False
        no_args_reason = "Script not found."

        nonexistent_passed = False
        nonexistent_reason = "Script not found."

        if organize_sh.exists() and organize_sh.is_file():
            # Check 12: run organize.sh with no args and check if it exits non-zero (0.3 marks)
            try:
                res_no_args = subprocess.run(
                    ["bash", "organize.sh"],
                    cwd=str(week_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res_no_args.returncode != 0:
                    no_args_passed = True
                    no_args_reason = f"Script exited non-zero ({res_no_args.returncode}) with no arguments."
                else:
                    no_args_reason = "Script exited successfully (0) even when no arguments were provided."
            except Exception as e:
                no_args_reason = f"Error executing organize.sh: {e}"

            # Check 13: run organize.sh /nonexistent and check if it exits non-zero (0.2 marks)
            try:
                res_nonexistent = subprocess.run(
                    ["bash", "organize.sh", "/nonexistent"],
                    cwd=str(week_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res_nonexistent.returncode != 0:
                    nonexistent_passed = True
                    nonexistent_reason = f"Script exited non-zero ({res_nonexistent.returncode}) for /nonexistent directory."
                else:
                    nonexistent_reason = "Script exited successfully (0) even for /nonexistent directory."
            except Exception as e:
                nonexistent_reason = f"Error executing organize.sh: {e}"

        checks.append(
            CheckResult(
                name="Error Handling Check (No Arguments)",
                passed=no_args_passed,
                marks=0.3 if no_args_passed else 0.0,
                max_marks=0.3,
                reason=no_args_reason,
                hint="Ensure that organize.sh exits with a non-zero code if it does not receive exactly one argument.",
            )
        )

        checks.append(
            CheckResult(
                name="Error Handling Check (Non-existent Directory)",
                passed=nonexistent_passed,
                marks=0.2 if nonexistent_passed else 0.0,
                max_marks=0.2,
                reason=nonexistent_reason,
                hint="Ensure that organize.sh exits with a non-zero code if the target directory does not exist.",
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
            feedback=f"Completed file organizer checks. Score: {total_score}/{total_max}",
        )
