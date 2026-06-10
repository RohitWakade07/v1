import re
from pathlib import Path
from graders.base_grader import BaseGrader, CheckResult, GradingResult


class Week2Grader(BaseGrader):
    def grade(self) -> GradingResult:
        checks = []

        # Get execution results from config
        exec_res = self.config.get("execution_result", {})
        exit_code = exec_res.get("exit_code")
        timed_out = exec_res.get("timed_out", False)
        oom_killed = exec_res.get("oom_killed", False)

        # Check 1: script exits with code 0 (1 mark)
        exit_passed = (exit_code == 0 and not timed_out and not oom_killed)
        exit_marks = 1.0 if exit_passed else 0.0
        exit_reason = "Script exited successfully."
        if timed_out:
            exit_reason = "Script execution timed out."
        elif oom_killed:
            exit_reason = "Script execution ran out of memory (OOM)."
        elif exit_code is not None and exit_code != 0:
            exit_reason = f"Script exited with non-zero exit code: {exit_code}."
        elif exit_code is None:
            exit_reason = "Script was not executed or crashed during startup."

        checks.append(
            CheckResult(
                name="Script Exit Status Check",
                passed=exit_passed,
                marks=exit_marks,
                max_marks=1.0,
                reason=exit_reason,
                hint="Make sure the script runs and exits cleanly (exit code 0).",
            )
        )

        # Check 2: report.txt is created (1 mark)
        report_path = self.workspace / "week-02" / "report.txt"
        report_exists = report_path.exists() and report_path.is_file()
        report_marks = 1.0 if report_exists else 0.0
        checks.append(
            CheckResult(
                name="Report Creation Check",
                passed=report_exists,
                marks=report_marks,
                max_marks=1.0,
                reason="report.txt was created successfully." if report_exists else "report.txt was not found.",
                hint="Ensure that your analyze.sh script redirects output to a file named report.txt inside week-02/.",
            )
        )

        # Read report and script contents for pattern analysis
        report_content = ""
        if report_exists:
            try:
                with open(report_path, "r", errors="ignore") as f:
                    report_content = f.read()
            except Exception as e:
                report_content = ""

        script_path = self.workspace / "week-02" / "analyze.sh"
        script_content = ""
        if script_path.exists() and script_path.is_file():
            try:
                with open(script_path, "r", errors="ignore") as f:
                    script_content = f.read()
            except Exception as e:
                script_content = ""

        # Check 3: report contains a number near 'total' or 'count' (0.5 marks)
        total_pattern = re.compile(r"(total|count)[^\d]{0,30}\b\d+\b", re.IGNORECASE)
        total_passed = bool(total_pattern.search(report_content))
        total_marks = 0.5 if total_passed else 0.0
        checks.append(
            CheckResult(
                name="Total Request Count Pattern Check",
                passed=total_passed,
                marks=total_marks,
                max_marks=0.5,
                reason="Found request count output." if total_passed else "Could not find a line containing 'total' or 'count' followed by a number.",
                hint="Make sure report.txt contains the total requests count with labels like 'Total Requests' or 'Count'.",
            )
        )

        # Check 4: report contains IP address pattern (0.5 marks)
        ip_pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        ip_passed = bool(ip_pattern.search(report_content))
        ip_marks = 0.5 if ip_passed else 0.0
        checks.append(
            CheckResult(
                name="IP Address Output Check",
                passed=ip_passed,
                marks=ip_marks,
                max_marks=0.5,
                reason="Found IP addresses in report." if ip_passed else "No IP address patterns found in report.",
                hint="Ensure your script extracts and displays the top IP addresses in the log.",
            )
        )

        # Check 5: report contains URL path pattern (0.5 marks)
        url_pattern = re.compile(r"/[a-zA-Z]")
        url_passed = bool(url_pattern.search(report_content))
        url_marks = 0.5 if url_passed else 0.0
        checks.append(
            CheckResult(
                name="URL Path Output Check",
                passed=url_passed,
                marks=url_marks,
                max_marks=0.5,
                reason="Found URL paths in report." if url_passed else "No URL paths found in report.",
                hint="Ensure your script extracts and displays the top URL paths requested.",
            )
        )

        # Check 6: report contains HTTP status code pattern (0.5 marks)
        status_pattern = re.compile(r"\b(200|40\d|50\d)\b")
        status_passed = bool(status_pattern.search(report_content))
        status_marks = 0.5 if status_passed else 0.0
        checks.append(
            CheckResult(
                name="HTTP Status Code Output Check",
                passed=status_passed,
                marks=status_marks,
                max_marks=0.5,
                reason="Found HTTP status code distribution in report." if status_passed else "No HTTP status code distribution found in report.",
                hint="Ensure your script counts and prints HTTP status codes like 200, 404, 500, etc.",
            )
        )

        # Check 7: script source contains pipe character (0.5 marks)
        pipe_passed = "|" in script_content
        pipe_marks = 0.5 if pipe_passed else 0.0
        checks.append(
            CheckResult(
                name="Source Code Pipe Character Check",
                passed=pipe_passed,
                marks=pipe_marks,
                max_marks=0.5,
                reason="Found pipeline character '|' in analyze.sh." if pipe_passed else "No pipeline character '|' found in analyze.sh.",
                hint="Use piping to chain commands like awk, sort, uniq, and head.",
            )
        )

        # Check 8: script source contains redirection (0.5 marks)
        redir_passed = (">" in script_content or ">>" in script_content)
        redir_marks = 0.5 if redir_passed else 0.0
        checks.append(
            CheckResult(
                name="Source Code Redirection Check",
                passed=redir_passed,
                marks=redir_marks,
                max_marks=0.5,
                reason="Found redirection operator '>' or '>>' in analyze.sh." if redir_passed else "No redirection operator found in analyze.sh.",
                hint="Use redirection to write or append output to report.txt.",
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
            feedback=f"Completed log analyzer checks. Score: {total_score}/{total_max}",
        )
