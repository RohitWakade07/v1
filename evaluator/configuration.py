import os

class Configuration:
    """Manages the configuration parameters for the local Python-Bash evaluator."""
    
    def __init__(self):
        # API Communication
        self.backend_url = os.getenv("EEYAN_BACKEND_URL", "http://localhost:8000")
        self.session_id = os.getenv("EEYAN_SESSION_ID", "")
        self.student_token = os.getenv("EEYAN_STUDENT_TOKEN", "")
        self.roll_number = os.getenv("EEYAN_ROLL_NUMBER", "22BEC001")
        
        # Security signing key
        # MUST match the PROOF_SIGNING_KEY in the backend setting
        self.signing_key = os.getenv(
            "EEYAN_SIGNING_KEY",
            "3ea77ef562113a93a15a613c7bf1d23b109f4dea557b572a2d52a44fbc3f823736f9a4bc18705cb2fbaead40556512ff40d4ce3d33e7e670c61aff25970512ba"
        )
        
        # Local workspace / environment
        self.workspace_dir = os.getenv("EEYAN_WORKSPACE_DIR", os.getcwd())
        self.scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
        self.state_file = os.path.join(self.workspace_dir, ".evaluator_state.json")
        
        # Verification details
        self.grader_version = "1.0.0"
        self.grader_binary_hash = os.getenv("EEYAN_GRADER_BINARY_HASH", "a" * 64)

    def validate(self) -> None:
        """Validates critical parameters."""
        if not self.session_id:
            raise ValueError("EEYAN_SESSION_ID must be set.")
        if not self.student_token:
            raise ValueError("EEYAN_STUDENT_TOKEN must be set.")
