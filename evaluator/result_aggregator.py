import hashlib
from typing import Dict, Any, List

class ResultAggregator:
    """Combines individual rule verification outcomes into unified packages."""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.artifact_hashes: Dict[str, str] = {}

    def add_result(self, rule_id: str, passed: bool, stdout: str, stderr: str, exit_code: int, score: float) -> None:
        """Adds a single validator rule execution outcome to the aggregator."""
        stdout_hash = hashlib.sha256(stdout.encode()).hexdigest() if stdout else None
        stderr_hash = hashlib.sha256(stderr.encode()).hexdigest() if stderr else None
        
        self.results[rule_id] = {
            "test_id": rule_id,
            "passed": passed,
            "stdout_hash": stdout_hash,
            "stderr_hash": stderr_hash,
            "exit_code": exit_code,
            "score": score if passed else 0.0
        }

    def record_artifact(self, filename: str, filepath: str) -> None:
        """Calculates and stores the SHA-256 hash of a checked artifact file."""
        import os
        if os.path.exists(filepath) and os.path.isfile(filepath):
            try:
                sha = hashlib.sha256()
                with open(filepath, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha.update(chunk)
                self.artifact_hashes[filename] = sha.hexdigest()
            except Exception:
                pass
        else:
            self.artifact_hashes[filename] = hashlib.sha256(filename.encode()).hexdigest()

    def get_summary(self) -> Dict[str, Any]:
        return {
            "results": self.results,
            "artifact_hashes": self.artifact_hashes
        }
