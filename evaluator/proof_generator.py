import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any
from evaluator.evaluator_logging import logger
from evaluator.configuration import Configuration
from evaluator.result_aggregator import ResultAggregator
from evaluator.challenge_parser import ChallengePackage

class ProofGenerator:
    """Collects metadata, serializes canonical payloads, and computes secure HMAC signatures."""

    def __init__(self, config: Configuration):
        self.config = config

    def generate_proof(self, challenge: ChallengePackage, aggregator: ResultAggregator) -> Dict[str, Any]:
        """Builds, canonizes, and signs the complete proof package."""
        logger.info("Assembling proof package details...")
        
        summary = aggregator.get_summary()
        
        proof_payload = {
            "session_id": str(challenge.session_id),
            "assignment_id": str(challenge.assignment_id),
            "student_id": str(self.config.roll_number),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nonce": str(challenge.nonce),
            "grader_binary_hash": str(self.config.grader_binary_hash),
            "results": summary["results"],
            "artifact_hashes": summary["artifact_hashes"]
        }
        
        # Canonical representation serialization (matching backend exactly)
        canonical = json.dumps(proof_payload, sort_keys=True, separators=(",", ":"))
        
        # Calculate HMAC-SHA256 signature
        logger.info("Computing proof HMAC signature...")
        signature = hmac.new(
            self.config.signing_key.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()
        
        proof_payload["hmac_signature"] = signature
        logger.info("Proof package successfully signed and compiled.")
        return proof_payload
