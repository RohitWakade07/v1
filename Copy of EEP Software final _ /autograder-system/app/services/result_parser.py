import json
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

class TestResult(BaseModel):
    name: str
    passed: bool
    message: str | None = None

class GraderResult(BaseModel):
    score: float = Field(ge=0, le=100)
    status: str
    feedback: str
    tests: list[TestResult] = []
    execution_time_ms: int | None = None

class ResultParser:
    @staticmethod
    def parse(results_dir: str) -> dict:
        """
        Strictly parses and validates the results.json file produced by the grading container.
        """
        results_file = Path(results_dir) / "results.json"
        
        if not results_file.exists():
            logger.warning(f"results.json not found in {results_dir}")
            return GraderResult(
                score=0,
                status="failed",
                feedback="Internal Error: No results produced. The code may have crashed or exhausted memory."
            ).model_dump()
            
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Validate against Pydantic schema
            parsed_result = GraderResult(**data)
            return parsed_result.model_dump()
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode results.json: {e}")
            return GraderResult(
                score=0,
                status="failed",
                feedback="Internal Error: Sandbox output was not valid JSON."
            ).model_dump()
        except ValidationError as e:
            logger.error(f"results.json schema validation failed: {e}")
            return GraderResult(
                score=0,
                status="failed",
                feedback="Internal Error: Sandbox output did not match expected schema."
            ).model_dump()
        except Exception as e:
            logger.error(f"Unexpected error reading results.json: {e}")
            return GraderResult(
                score=0,
                status="failed",
                feedback=f"Internal Error: {str(e)}"
            ).model_dump()
