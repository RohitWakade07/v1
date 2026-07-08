"""
Week 12 Grader: Final Capstone – Semantic Search Engine
"""
import json
import logging
from graders.base_grader import BaseGrader, GradingResult, CheckResult

logger = logging.getLogger(__name__)

MAX_POINTS = {
    "engineering_quality": 20.0,
    "dataset": 10.0,
    "persistent_inverted_index": 20.0,
    "ranking": 15.0,
    "query_handling": 35.0,
}

HINTS = {
    "engineering_quality": "Include README.md, requirements.txt, and use modular code with ≥3 Python files.",
    "dataset": "Provide a corpus/ directory with ≥50 JSON documents, each having a 'content' field.",
    "persistent_inverted_index": "build_index.py must create a persistent index file (index.json, index.pkl, etc.).",
    "ranking": "Search results should be ranked by relevance (e.g., TF-IDF cosine similarity).",
    "query_handling": "query.py should handle multiple consecutive queries in a loop and exit on 'quit'.",
}


class Week12Grader(BaseGrader):
    def grade(self) -> GradingResult:
        max_score = 100.0
        exec_res = self.config.get("execution_result", {})
        stdout = exec_res.get("stdout", "")
        stderr = exec_res.get("stderr", "")

        try:
            start = stdout.find("{")
            end = stdout.rfind("}")
            if start != -1 and end != -1:
                result_data = json.loads(stdout[start:end + 1])
            else:
                raise json.JSONDecodeError("No JSON", stdout, 0)
        except json.JSONDecodeError:
            return GradingResult(
                score=0.0, max_score=max_score, passed=False,
                checks=[CheckResult("Execution", False, 0.0, max_score, "No JSON output from test wrapper", "Fix script crash or missing dependencies")],
                feedback=f"stdout:\n{stdout[:500]}\nstderr:\n{stderr[:500]}"
            )

        breakdown = result_data.get("breakdown", {})
        feedback = result_data.get("feedback", [])
        bonus = result_data.get("bonus_features", [])

        checks = []
        total = 0.0
        for k, max_p in MAX_POINTS.items():
            pts = float(breakdown.get(k, 0.0))
            passed = pts >= max_p - 0.01
            total += pts
            # Find relevant feedback for this check
            rel = [m for m in feedback if k.replace("_", " ") in m.lower() or k.split("_")[0] in m.lower()]
            reason = rel[0] if rel else f"{pts:.0f}/{max_p:.0f} pts"
            checks.append(CheckResult(k.replace("_", " ").title(), passed, pts, max_p, reason, HINTS.get(k, "")))

        bonus_txt = f"\n\nBonus: {', '.join(bonus)}" if bonus else ""
        return GradingResult(total, max_score, total >= 60.0, checks, "\n".join(f"- {m}" for m in feedback) + bonus_txt)
