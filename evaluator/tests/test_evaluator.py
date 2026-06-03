import os
import json
import pytest
import hmac
import hashlib
from evaluator.configuration import Configuration
from evaluator.state_machine import StateMachine, State
from evaluator.challenge_parser import ChallengeParser, ChallengePackage
from evaluator.validator_registry import ValidatorRegistry
from evaluator.result_aggregator import ResultAggregator
from evaluator.proof_generator import ProofGenerator

def test_configuration_loading(tmp_path):
    os.environ["EEYAN_SESSION_ID"] = "session-uuid-123"
    os.environ["EEYAN_STUDENT_TOKEN"] = "jwt-student-token"
    os.environ["EEYAN_ROLL_NUMBER"] = "22BEC009"
    
    config = Configuration()
    config.workspace_dir = str(tmp_path)
    config.state_file = os.path.join(str(tmp_path), ".state.json")
    
    config.validate()
    
    assert config.session_id == "session-uuid-123"
    assert config.student_token == "jwt-student-token"
    assert config.roll_number == "22BEC009"

def test_state_machine_transitions(tmp_path):
    state_file = os.path.join(str(tmp_path), ".state.json")
    sm = StateMachine(state_file)
    
    assert sm.current_state == State.CREATED
    
    sm.transition_to(State.CHALLENGE_ISSUED, "Challenge fetched")
    assert sm.current_state == State.CHALLENGE_ISSUED
    
    sm.transition_to(State.RUNNING, "Grader started")
    assert sm.current_state == State.RUNNING
    
    # Check invalid transition
    with pytest.raises(ValueError):
        sm.transition_to(State.VERIFIED, "Direct verify")
        
    # Check persistence
    sm2 = StateMachine(state_file)
    assert sm2.current_state == State.RUNNING
    assert len(sm2.history) == 3

def test_challenge_parser():
    challenge_payload = {
        "session": {
            "session_id": "session-1",
            "student_id": "22BEC001",
            "nonce": "nonce-1",
            "started_at": "2026-06-02T10:00:00"
        },
        "assignment": {
            "assignment_id": "assign-1",
            "slug": "slug-1",
            "title": "Title 1",
            "category": "artifact_validation",
            "max_score": 100.0
        },
        "grader": {
            "grader_id": "grader-1",
            "name": "Grader Name",
            "version": "1.0.0",
            "binary_hash": "graderhash123"
        },
        "execution_constraints": {
            "timeout_seconds": 150
        },
        "validation_rules": [
            {
                "rule_id": "rule_1",
                "type": "file_exists",
                "target": "output.txt",
                "points": 50.0
            }
        ]
    }
    
    pkg = ChallengeParser.parse(challenge_payload)
    assert pkg.session_id == "session-1"
    assert pkg.slug == "slug-1"
    assert pkg.timeout_seconds == 150
    assert len(pkg.rules) == 1
    assert pkg.rules[0].rule_id == "rule_1"
    assert pkg.rules[0].points == 50.0

def test_validator_registry():
    from evaluator.validators.file_exists import FileExistsValidator
    
    val_class = ValidatorRegistry.get_validator("file_exists")
    assert val_class == FileExistsValidator
    
    val_none = ValidatorRegistry.get_validator("non_existent_validator")
    assert val_none is None

def test_result_aggregator_and_proof_generator(tmp_path):
    config = Configuration()
    config.signing_key = "key123"
    config.roll_number = "22BEC001"
    config.grader_binary_hash = "graderhash123"
    
    agg = ResultAggregator()
    agg.add_result(
        rule_id="rule_1",
        passed=True,
        stdout="success_stdout",
        stderr="",
        exit_code=0,
        score=50.0
    )
    
    challenge_payload = {
        "session": {"session_id": "sess-1", "student_id": "22BEC001", "nonce": "nonce-1"},
        "assignment": {"assignment_id": "assign-1", "slug": "slug-1", "title": "Title 1", "category": "artifact_validation", "max_score": 100.0},
        "grader": {"grader_id": "grader-1", "name": "Grader Name", "version": "1.0.0", "binary_hash": "graderhash123"},
        "execution_constraints": {},
        "validation_rules": []
    }
    challenge = ChallengeParser.parse(challenge_payload)
    
    proof_gen = ProofGenerator(config)
    proof = proof_gen.generate_proof(challenge, aggregator=agg)
    
    assert proof["session_id"] == "sess-1"
    assert proof["nonce"] == "nonce-1"
    assert "hmac_signature" in proof
    
    payload_to_sign = {k: v for k, v in proof.items() if k != "hmac_signature"}
    canonical = json.dumps(payload_to_sign, sort_keys=True, separators=(",", ":"))
    expected_sig = hmac.new(
        b"key123",
        canonical.encode(),
        hashlib.sha256
    ).hexdigest()
    
    assert proof["hmac_signature"] == expected_sig
