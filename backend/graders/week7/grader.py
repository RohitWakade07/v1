"""
Week 7 Grader: Web Scraper — collect_wiki.py
=============================================
Students write collect_wiki.py that scrapes Wikipedia pages from urls.txt
and stores results as JSON files in corpus/.

Scoring (100 pts):
  execution        : 20 pts — script exits 0
  corpus_dir       : 20 pts — corpus/ has ≥ 3 JSON files
  json_schema      : 30 pts — each file has title, url, text keys
  content_quality  : 30 pts — text is non-trivial (≥ 50 words/doc)
"""
import json
import logging
from graders.base_grader import BaseGrader, GradingResult, CheckResult

logger = logging.getLogger(__name__)

MAX_POINTS: dict[str, float] = {
    "execution":       20.0,
    "corpus_dir":      20.0,
    "json_schema":     30.0,
    "content_quality": 30.0,
}

HINTS: dict[str, str] = {
    "execution":       "Ensure collect_wiki.py runs without crashing. Handle HTTP errors gracefully.",
    "corpus_dir":      "Save each scraped page as corpus/<slug>.json with at least 3 files.",
    "json_schema":     'Each JSON file must have keys: "title", "url", "text".',
    "content_quality": "Ensure text extraction captures meaningful content (≥ 50 words per page).",
}


class Week7Grader(BaseGrader):
    """
    Week 7: Web Scraper.
    Parses JSON report from test_wrapper.py.
    """

    def grade(self) -> GradingResult:
        max_score = 100.0
        exec_res  = self.config.get("execution_result", {})
        stdout    = exec_res.get("stdout", "")
        stderr    = exec_res.get("stderr", "")
        timed_out = exec_res.get("timed_out", False)
        oom       = exec_res.get("oom_killed", False)

        if timed_out or oom:
            reason = "Execution timed out (>60s)." if timed_out else "Process killed (OOM)."
            return GradingResult(
                score=0.0, max_score=max_score, passed=False,
                checks=[CheckResult(
                    name="Sandbox Execution",
                    passed=False, marks=0.0, max_marks=max_score,
                    reason=reason,
                    hint="Add time.sleep(1) between requests and ensure no infinite loops.",
                )],
                feedback=reason,
            )

        # Parse JSON
        result_data: dict = {}
        try:
            start = stdout.find("{")
            end   = stdout.rfind("}")
            if start != -1 and end != -1:
                result_data = json.loads(stdout[start:end + 1])
            else:
                raise json.JSONDecodeError("No JSON", stdout, 0)
        except json.JSONDecodeError:
            logger.error("Week7: failed to parse wrapper JSON. stdout=%s", stdout[:500])
            return GradingResult(
                score=0.0, max_score=max_score, passed=False,
                checks=[CheckResult(
                    name="Test Wrapper Output",
                    passed=False, marks=0.0, max_marks=max_score,
                    reason="Test wrapper did not produce valid JSON output.",
                    hint="Run: python collect_wiki.py and check it runs without crashing.",
                )],
                feedback=f"stdout: {stdout[:500]}\nstderr: {stderr[:500]}",
            )

        breakdown        = result_data.get("breakdown", {})
        feedback_msgs    = result_data.get("feedback", [])
        bonus_features   = result_data.get("bonus_features", [])

        checks: list[CheckResult] = []
        total_score = 0.0

        for key, max_pts in MAX_POINTS.items():
            pts    = float(breakdown.get(key, 0.0))
            passed = pts >= max_pts - 0.01
            total_score += pts

            relevant = [m for m in feedback_msgs if key.replace("_", " ") in m.lower()
                        or key.split("_")[0] in m.lower()]
            reason = relevant[0] if relevant else (
                f"Full marks ({pts:.0f}/{max_pts:.0f})" if passed
                else f"{pts:.0f}/{max_pts:.0f} points"
            )

            checks.append(CheckResult(
                name=key.replace("_", " ").title(),
                passed=passed,
                marks=pts,
                max_marks=max_pts,
                reason=reason,
                hint="" if passed else HINTS.get(key, ""),
            ))

        bonus_text = ""
        if bonus_features:
            bonus_text = "\n\n🎉 Bonus: " + ", ".join(bonus_features)

        return GradingResult(
            score=round(total_score, 2),
            max_score=max_score,
            passed=total_score >= 60.0,
            checks=checks,
            feedback="\n".join(f"- {m}" for m in feedback_msgs) + bonus_text,
        )
