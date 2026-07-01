"""
Week 6 Grader: Interactive Python CLI Analyzer
================================================
Students submit analyze.py — an interactive CLI tool that:
  - Reads .txt files from a folder
  - Accepts commands: stats <filename>, search <word>, top <N> <filename>, quit

Test approach:
  1. The test_wrapper.py asset runs the student's analyze.py using subprocess
     with piped stdin for each command sequence
  2. The wrapper outputs a JSON blob on stdout with: breakdown + feedback
  3. This grader parses that JSON and produces structured CheckResult objects.

Scoring (100 pts total):
  repo_structure    : 30 pts — README.md (≥30 words) + requirements.txt
  stats_command     : 20 pts — correct line/word/char counts
  search_command    : 20 pts — finds word across all files
  top_command       : 10 pts — returns top N words
  quit_command      : 10 pts — exits cleanly (exit code 0)
  error_handling    : 10 pts — handles bad input gracefully

Adapted from external: I-M-Sharma/eep1-grader Week 6 (pexpect approach
translated to subprocess stdin pipe which works in our Docker sandbox model).
"""
import json
import logging
from graders.base_grader import BaseGrader, GradingResult, CheckResult

logger = logging.getLogger(__name__)

# Expected max points per category (must match test_wrapper.py output keys)
MAX_POINTS: dict[str, float] = {
    "repo_structure":  30.0,
    "stats_command":   20.0,
    "search_command":  20.0,
    "top_command":     10.0,
    "quit_command":    10.0,
    "error_handling":  10.0,
}

HINTS: dict[str, str] = {
    "repo_structure":  "Include README.md (≥ 30 words) and requirements.txt in the ZIP.",
    "stats_command":   "stats <filename>: print Lines, Words, Characters for the given file.",
    "search_command":  "search <word>: print filenames containing the word (case-insensitive).",
    "top_command":     "top <N> <filename>: print the N most frequent words and their counts.",
    "quit_command":    "quit: exit the program with exit code 0.",
    "error_handling":  "Handle unknown commands, missing files, and bad input gracefully.",
}


class Week6Grader(BaseGrader):
    """
    Week 6: Interactive Python Text Analyzer.
    Parses the JSON report from test_wrapper.py.
    """

    def grade(self) -> GradingResult:
        max_score = 100.0
        exec_res  = self.config.get("execution_result", {})
        stdout    = exec_res.get("stdout", "")
        stderr    = exec_res.get("stderr", "")
        timed_out = exec_res.get("timed_out", False)
        oom       = exec_res.get("oom_killed", False)

        # ── Handle sandbox-level failures ─────────────────────────────────
        if timed_out or oom:
            reason = "Execution timed out." if timed_out else "Process killed (OOM)."
            hint   = (
                "Your program may be stuck in an infinite loop or not handling 'quit'."
                if timed_out else
                "Reduce memory usage — avoid loading large files entirely into RAM."
            )
            return GradingResult(
                score=0.0, max_score=max_score, passed=False,
                checks=[CheckResult(
                    name="Sandbox Execution",
                    passed=False, marks=0.0, max_marks=max_score,
                    reason=reason, hint=hint,
                )],
                feedback=f"{reason}\nStderr: {stderr[:500]}",
            )

        # ── Parse JSON report from test_wrapper ───────────────────────────
        result_data: dict = {}
        try:
            # Find outermost JSON object in stdout
            start = stdout.find("{")
            end   = stdout.rfind("}")
            if start != -1 and end != -1:
                result_data = json.loads(stdout[start:end + 1])
            else:
                raise json.JSONDecodeError("No JSON object found", stdout, 0)
        except json.JSONDecodeError:
            logger.error("Week6: failed to parse test_wrapper JSON. stdout=%s", stdout[:500])
            return GradingResult(
                score=0.0, max_score=max_score, passed=False,
                checks=[CheckResult(
                    name="Test Wrapper Output",
                    passed=False, marks=0.0, max_marks=max_score,
                    reason="Grader wrapper did not produce valid JSON. Check your analyze.py runs without crashing.",
                    hint="Run: echo -e 'stats file1.txt\\nquit' | python analyze.py test_data/",
                )],
                feedback=f"Raw stdout (first 1000 chars):\n{stdout[:1000]}\n\nStderr:\n{stderr[:500]}",
            )

        # ── Build individual CheckResult objects ─────────────────────────
        breakdown        = result_data.get("breakdown", {})
        feedback_messages: list[str] = result_data.get("feedback", [])
        bonus_features:  list[str] = result_data.get("bonus_features", [])

        checks: list[CheckResult] = []
        total_score = 0.0

        for key, max_pts in MAX_POINTS.items():
            pts    = float(breakdown.get(key, 0.0))
            passed = abs(pts - max_pts) < 0.01  # float-safe equality
            total_score += pts

            # Find the most relevant feedback message for this check
            relevant = [
                msg for msg in feedback_messages
                if key.replace("_", " ") in msg.lower()
                or key.split("_")[0] in msg.lower()
            ]
            reason = relevant[0] if relevant else (
                f"Passed ({pts:.0f}/{max_pts:.0f} pts)" if passed
                else f"Failed ({pts:.0f}/{max_pts:.0f} pts)"
            )

            checks.append(CheckResult(
                name=key.replace("_", " ").title(),
                passed=passed,
                marks=pts,
                max_marks=max_pts,
                reason=reason,
                hint="" if passed else HINTS.get(key, ""),
            ))

        # ── Bonus feedback ─────────────────────────────────────────────────
        bonus_text = ""
        if bonus_features:
            bonus_text = "\n\n🎉 Bonus Features Detected:\n" + "\n".join(f"  • {f}" for f in bonus_features)

        formatted_feedback = (
            "\n".join(f"- {msg}" for msg in feedback_messages)
            + bonus_text
        )

        return GradingResult(
            score=round(total_score, 2),
            max_score=max_score,
            passed=total_score >= 60.0,
            checks=checks,
            feedback=formatted_feedback,
        )
