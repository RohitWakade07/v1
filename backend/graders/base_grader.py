from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    passed: bool
    marks: float
    max_marks: float
    reason: str
    hint: str


@dataclass
class GradingResult:
    score: float
    max_score: float
    passed: bool
    checks: list[CheckResult] = field(default_factory=list)
    feedback: str = ""
    ai_feedback: str = ""


class BaseGrader:
    def __init__(self, workspace: str, assets_path: str, config: dict[str, Any]):
        self.workspace = Path(workspace)
        self.assets_path = Path(assets_path)
        self.config = config

    def grade(self) -> GradingResult:
        raise NotImplementedError("Graders must implement the grade() method.")
