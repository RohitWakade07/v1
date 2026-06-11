"""
Week 2 Grader: Command-Line Log Analyzer
=========================================
Test harness approach:
  1. A known server.log is injected as an asset (we know its exact contents).
  2. The student's analyze.sh is executed against that log.
  3. The generated report.txt is checked for EXACT expected values
     that we pre-computed from the same log.

Expected values from the injected server.log:
  - Total requests       : 20
  - Top IP               : 192.168.1.100  (8 hits)
  - Second IP            : 10.0.0.5       (7 hits)
  - Top URL              : /index.html     (8 hits)
  - Status code 200 count: 14
  - Status code 404 count: 3
  - Status code 500 count: 3
"""
import re
from pathlib import Path
from graders.base_grader import BaseGrader, CheckResult, GradingResult


class Week2Grader(BaseGrader):

    # ── Pre-computed expected values from the injected server.log ──────────
    EXPECTED_TOTAL = 20
    EXPECTED_TOP_IP = "192.168.1.100"
    EXPECTED_SECOND_IP = "10.0.0.5"
    EXPECTED_TOP_URL = "/index.html"
    EXPECTED_STATUS_200 = 14
    EXPECTED_STATUS_404 = 3
    EXPECTED_STATUS_500 = 3

    def grade(self) -> GradingResult:
        checks = []

        exec_res = self.config.get("execution_result", {})
        exit_code = exec_res.get("exit_code")
        timed_out = exec_res.get("timed_out", False)
        oom_killed = exec_res.get("oom_killed", False)

        # ── Check 1: Script ran successfully ──────────────────────────────
        exit_passed = (exit_code == 0 and not timed_out and not oom_killed)
        if timed_out:
            exit_reason = "Script execution timed out."
        elif oom_killed:
            exit_reason = "Script execution ran out of memory (OOM)."
        elif exit_code is not None and exit_code != 0:
            exit_reason = f"Script exited with non-zero exit code: {exit_code}."
        elif exit_code is None:
            exit_reason = "Script was not executed or crashed during startup."
        else:
            exit_reason = "Script exited successfully."

        checks.append(CheckResult(
            name="Script Exit Status",
            passed=exit_passed,
            marks=1.0 if exit_passed else 0.0,
            max_marks=1.0,
            reason=exit_reason,
            hint="Ensure analyze.sh runs and exits with code 0.",
        ))

        # ── Check 2: report.txt was created ───────────────────────────────
        report_path = self.workspace / "report.txt"
        report_exists = report_path.exists() and report_path.is_file()
        checks.append(CheckResult(
            name="Report File Created",
            passed=report_exists,
            marks=0.5 if report_exists else 0.0,
            max_marks=0.5,
            reason="report.txt found." if report_exists else "report.txt not found.",
            hint="Redirect your analysis output to report.txt.",
        ))

        report_content = ""
        if report_exists:
            try:
                report_content = report_path.read_text(errors="ignore")
            except Exception:
                pass

        if not report_exists:
            # Fill remaining checks as failed so totals are consistent
            for _ in range(5):
                checks.append(CheckResult(
                    name="(skipped)", passed=False, marks=0.0, max_marks=0.5,
                    reason="report.txt missing; cannot verify output.",
                    hint="Create report.txt first.",
                ))
        else:
            # ── Check 3: Total request count is correct (exact) ───────────
            total_numbers = re.findall(r"\b(\d+)\b", report_content)
            found_total = str(self.EXPECTED_TOTAL) in total_numbers
            checks.append(CheckResult(
                name=f"Total Request Count (expected {self.EXPECTED_TOTAL})",
                passed=found_total,
                marks=0.5 if found_total else 0.0,
                max_marks=0.5,
                reason=f"Found '{self.EXPECTED_TOTAL}' in report." if found_total
                       else f"'{self.EXPECTED_TOTAL}' not found in report. Numbers present: {total_numbers[:10]}",
                hint=f"Your report should contain the total request count: {self.EXPECTED_TOTAL}.",
            ))

            # ── Check 4: Top IP address is correct ───────────────────────
            top_ip_found = self.EXPECTED_TOP_IP in report_content
            checks.append(CheckResult(
                name=f"Top IP Address (expected {self.EXPECTED_TOP_IP})",
                passed=top_ip_found,
                marks=0.5 if top_ip_found else 0.0,
                max_marks=0.5,
                reason=f"'{self.EXPECTED_TOP_IP}' found in report." if top_ip_found
                       else f"'{self.EXPECTED_TOP_IP}' not found in report.",
                hint=f"The most frequent IP in the log is {self.EXPECTED_TOP_IP} with 8 requests.",
            ))

            # ── Check 5: Top URL path is correct ─────────────────────────
            top_url_found = self.EXPECTED_TOP_URL in report_content
            checks.append(CheckResult(
                name=f"Top URL Path (expected {self.EXPECTED_TOP_URL})",
                passed=top_url_found,
                marks=0.5 if top_url_found else 0.0,
                max_marks=0.5,
                reason=f"'{self.EXPECTED_TOP_URL}' found in report." if top_url_found
                       else f"'{self.EXPECTED_TOP_URL}' not found in report.",
                hint=f"The most requested URL is {self.EXPECTED_TOP_URL} with 8 hits.",
            ))

            # ── Check 6: Status code 200 count is correct ─────────────────
            status_200_ok = str(self.EXPECTED_STATUS_200) in report_content
            checks.append(CheckResult(
                name=f"HTTP 200 Count (expected {self.EXPECTED_STATUS_200})",
                passed=status_200_ok,
                marks=0.5 if status_200_ok else 0.0,
                max_marks=0.5,
                reason=f"Found '{self.EXPECTED_STATUS_200}' in report." if status_200_ok
                       else f"Expected count {self.EXPECTED_STATUS_200} for HTTP 200 not found in report.",
                hint=f"There are {self.EXPECTED_STATUS_200} HTTP 200 responses in the log.",
            ))

            # ── Check 7: Both 4xx and 5xx codes appear ────────────────────
            has_404 = "404" in report_content
            has_500 = "500" in report_content
            error_codes_ok = has_404 and has_500
            checks.append(CheckResult(
                name="Error HTTP Status Codes Present (404 and 500)",
                passed=error_codes_ok,
                marks=0.5 if error_codes_ok else 0.0,
                max_marks=0.5,
                reason="Both 404 and 500 status codes reported." if error_codes_ok
                       else f"Missing: {'404 ' if not has_404 else ''}{'500' if not has_500 else ''}",
                hint="Your report should include 404 (3 occurrences) and 500 (3 occurrences) codes.",
            ))

        # ── Bonus: pipe and redirection technique checks ──────────────────
        script_path = self.workspace / "analyze.sh"
        script_content = ""
        if script_path.exists():
            try:
                script_content = script_path.read_text(errors="ignore")
            except Exception:
                pass

        pipe_passed = "|" in script_content
        checks.append(CheckResult(
            name="Uses Pipe Operator in Script",
            passed=pipe_passed,
            marks=0.3 if pipe_passed else 0.0,
            max_marks=0.3,
            reason="Found '|' in analyze.sh." if pipe_passed else "No pipe '|' found in analyze.sh.",
            hint="Chain commands with pipes: awk | sort | uniq | head.",
        ))

        redir_passed = (">" in script_content)
        checks.append(CheckResult(
            name="Uses Output Redirection in Script",
            passed=redir_passed,
            marks=0.2 if redir_passed else 0.0,
            max_marks=0.2,
            reason="Found '>' redirection in analyze.sh." if redir_passed else "No '>' found in analyze.sh.",
            hint="Use '>' or '>>' to write output to report.txt.",
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
            feedback=f"Log analyzer checks complete. Score: {total_score:.2f}/{total_max:.2f}",
        )
