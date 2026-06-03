import json
import os
from datetime import datetime
from typing import List, Dict, Any
from evaluator.evaluator_logging import logger

class State:
    CREATED = "CREATED"
    CHALLENGE_ISSUED = "CHALLENGE_ISSUED"
    RUNNING = "RUNNING"
    PROOF_GENERATED = "PROOF_GENERATED"
    PROOF_SUBMITTED = "PROOF_SUBMITTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

class StateMachine:
    """Strict state machine enforcing transitions and maintaining execution history."""
    
    VALID_TRANSITIONS = {
        State.CREATED: [State.CHALLENGE_ISSUED, State.FAILED, State.ABORTED],
        State.CHALLENGE_ISSUED: [State.RUNNING, State.FAILED, State.ABORTED],
        State.RUNNING: [State.PROOF_GENERATED, State.FAILED, State.ABORTED],
        State.PROOF_GENERATED: [State.PROOF_SUBMITTED, State.FAILED],
        State.PROOF_SUBMITTED: [State.VERIFIED, State.FAILED],
        State.VERIFIED: [],
        State.FAILED: [],
        State.ABORTED: []
    }

    def __init__(self, state_file_path: str):
        self.state_file_path = state_file_path
        self.current_state = State.CREATED
        self.history: List[Dict[str, Any]] = []
        self._record_transition(State.CREATED, "Session initialized")
        self.load()

    def transition_to(self, new_state: str, reason: str = "") -> None:
        """Transitions to a new state if valid under transition policies."""
        allowed = self.VALID_TRANSITIONS.get(self.current_state, [])
        if new_state not in allowed and new_state != State.FAILED:
            msg = f"Invalid state transition from {self.current_state} to {new_state}."
            logger.error(msg)
            raise ValueError(msg)
            
        old_state = self.current_state
        self.current_state = new_state
        self._record_transition(new_state, f"Transition from {old_state}. Reason: {reason}")
        self.save()
        logger.info(f"State transition: {old_state} -> {new_state} ({reason})")

    def _record_transition(self, state: str, reason: str) -> None:
        self.history.append({
            "state": state,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        })

    def save(self) -> None:
        """Saves current state and history to disk for resumption capability."""
        try:
            with open(self.state_file_path, "w") as f:
                json.dump({
                    "current_state": self.current_state,
                    "history": self.history
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state machine to disk: {e}")

    def load(self) -> None:
        """Loads state from disk if exists."""
        if os.path.exists(self.state_file_path):
            try:
                with open(self.state_file_path, "r") as f:
                    data = json.load(f)
                    self.current_state = data.get("current_state", State.CREATED)
                    self.history = data.get("history", self.history)
                logger.info(f"Loaded state machine from disk. Current state: {self.current_state}")
            except Exception as e:
                logger.error(f"Failed to load state machine from disk: {e}")
