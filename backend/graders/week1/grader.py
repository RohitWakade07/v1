"""
Week 1 Grader: Workspace Setup
================================
Students submit a ZIP containing a commands.txt file with simple shell
commands (mkdir, echo, etc.) that set up a workspace. The grader:
  1. Runs commands.txt via bash inside a container
  2. Checks exit code
  3. Validates the resulting filesystem structure
"""
from pathlib import Path
from graders.base_grader import BaseGrader, CheckResult, GradingResult


class Week1Grader(BaseGrader):
    def grade(self) -> GradingResult:
        checks = []

        # Check 1: Command Execution (1.0 marks)
        exec_res = self.config.get("execution_result", {})
        exit_code = exec_res.get("exit_code")
        timed_out = exec_res.get("timed_out", False)
        oom_killed = exec_res.get("oom_killed", False)

        if timed_out:
            exec_reason = "Commands timed out."
        elif oom_killed:
            exec_reason = "Commands ran out of memory."
        elif exit_code is not None and exit_code != 0:
            exec_reason = f"Commands exited with non-zero code: {exit_code}."
        elif exit_code is None:
            exec_reason = "Commands were not executed or crashed."
        else:
            exec_reason = "All commands executed successfully."

        passed_exec = (exit_code == 0 and not timed_out and not oom_killed)
        checks.append(
            CheckResult(
                name="Command Execution",
                passed=passed_exec,
                marks=1.0 if passed_exec else 0.0,
                max_marks=1.0,
                reason=exec_reason,
                hint="Ensure your commands.txt contains valid shell commands and has no syntax errors." if not passed_exec else "",
            )
        )

        eep_dir = self.workspace / "eep-software"

        # Check 2: 12 week directories exist (0.1 marks each, max 1.2 marks)
        week_dirs_passed = 0
        missing_weeks = []
        for i in range(1, 13):
            week_path = eep_dir / f"week-{i:02d}"
            if week_path.exists() and week_path.is_dir():
                week_dirs_passed += 1
            else:
                missing_weeks.append(f"week-{i:02d}")

        week_dirs_marks = round(week_dirs_passed * 0.1, 2)
        checks.append(
            CheckResult(
                name="Weekly Directories Check",
                passed=(week_dirs_passed == 12),
                marks=week_dirs_marks,
                max_marks=1.2,
                reason=f"Found {week_dirs_passed}/12 weekly directories.",
                hint=f"Ensure directories {', '.join(missing_weeks)} exist inside eep-software/" if missing_weeks else "All weekly directories exist.",
            )
        )

        # Check 3: notes/, scripts/, capstone/ directories exist (0.2 marks each, max 0.6 marks)
        struct_dirs_passed = 0
        missing_struct = []
        for dname in ["notes", "scripts", "capstone"]:
            dpath = eep_dir / dname
            if dpath.exists() and dpath.is_dir():
                struct_dirs_passed += 1
            else:
                missing_struct.append(dname)

        struct_dirs_marks = round(struct_dirs_passed * 0.2, 2)
        checks.append(
            CheckResult(
                name="Structural Directories Check",
                passed=(struct_dirs_passed == 3),
                marks=struct_dirs_marks,
                max_marks=0.6,
                reason=f"Found {struct_dirs_passed}/3 structural directories.",
                hint=f"Ensure directories {', '.join(missing_struct)} exist inside eep-software/" if missing_struct else "All structural directories exist.",
            )
        )

        # Check 4: each weekly directory contains a README.md (0.1 marks each, max 1.2 marks)
        readmes_passed = 0
        missing_readmes = []
        for i in range(1, 13):
            readme_path = eep_dir / f"week-{i:02d}" / "README.md"
            if readme_path.exists() and readme_path.is_file():
                readmes_passed += 1
            else:
                missing_readmes.append(f"week-{i:02d}/README.md")

        readmes_marks = round(readmes_passed * 0.1, 2)
        checks.append(
            CheckResult(
                name="Weekly READMEs Check",
                passed=(readmes_passed == 12),
                marks=readmes_marks,
                max_marks=1.2,
                reason=f"Found {readmes_passed}/12 weekly README.md files.",
                hint=f"Ensure files {', '.join(missing_readmes)} exist" if missing_readmes else "All weekly README.md files exist.",
            )
        )

        # Check 5: workspace-report.txt exists and is non-empty (0.5 marks)
        report_path = eep_dir / "workspace-report.txt"
        report_passed = False
        report_reason = "workspace-report.txt not found."
        report_hint = "Add a command to create workspace-report.txt inside eep-software/."
        report_marks = 0.0

        if report_path.exists() and report_path.is_file():
            if report_path.stat().st_size > 0:
                report_passed = True
                report_reason = "workspace-report.txt exists and is non-empty."
                report_hint = ""
                report_marks = 0.5
            else:
                report_reason = "workspace-report.txt is empty."
                report_hint = "Use echo or printf to write content into workspace-report.txt."

        checks.append(
            CheckResult(
                name="Workspace Report Check",
                passed=report_passed,
                marks=report_marks,
                max_marks=0.5,
                reason=report_reason,
                hint=report_hint,
            )
        )

        # Check 6: .bashrc exists at submission root with at least 2 alias definitions (0.5 marks)
        bashrc_path = self.workspace / ".bashrc"
        bashrc_passed = False
        bashrc_reason = ".bashrc not found at the submission root."
        bashrc_hint = "Add commands to create a .bashrc file with at least 2 aliases."
        bashrc_marks = 0.0

        if bashrc_path.exists() and bashrc_path.is_file():
            try:
                content = bashrc_path.read_text(errors="ignore")
                alias_lines = [
                    line for line in content.splitlines()
                    if line.strip().startswith("alias ")
                ]
                if len(alias_lines) >= 2:
                    bashrc_passed = True
                    bashrc_reason = f"Found {len(alias_lines)} alias definition(s) in .bashrc."
                    bashrc_hint = ""
                    bashrc_marks = 0.5
                else:
                    bashrc_reason = f"Found only {len(alias_lines)} alias definition(s) in .bashrc (need at least 2)."
                    bashrc_hint = "Add at least two aliases (e.g. alias ll='ls -al') to .bashrc."
            except Exception as e:
                bashrc_reason = f"Failed to read .bashrc: {e}"

        checks.append(
            CheckResult(
                name="Bash Configuration (Aliases) Check",
                passed=bashrc_passed,
                marks=bashrc_marks,
                max_marks=0.5,
                reason=bashrc_reason,
                hint=bashrc_hint,
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
            feedback=f"Completed workspace setup checks. Score: {total_score}/{total_max}",
        )
