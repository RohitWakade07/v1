from typing import Dict, Any, List

class ValidationRule:
    """Represents a single validation task extracted from the challenge config."""
    
    def __init__(self, rule_dict: Dict[str, Any]):
        self.rule_id = rule_dict.get("rule_id", "unknown_rule")
        self.type = rule_dict.get("type", "unknown_type")
        self.target = rule_dict.get("target", "")
        self.points = float(rule_dict.get("points", 0.0))
        self.metadata = rule_dict.get("metadata", {})

class ChallengePackage:
    """Encapsulates parsed, type-safe assignment configurations and constraints."""
    
    def __init__(self, raw_data: Dict[str, Any]):
        # Parse Session Metadata
        session_data = raw_data.get("session", {})
        self.session_id = session_data.get("session_id", "")
        self.student_id = session_data.get("student_id", "")
        self.nonce = session_data.get("nonce", "")
        
        # Parse Assignment Metadata
        assignment_data = raw_data.get("assignment", {})
        self.assignment_id = assignment_data.get("assignment_id", "")
        self.slug = assignment_data.get("slug", "")
        self.title = assignment_data.get("title", "")
        self.category = assignment_data.get("category", "")
        self.max_score = float(assignment_data.get("max_score", 100.0))
        
        # Parse Grader Version details
        grader_data = raw_data.get("grader", {})
        self.grader_id = grader_data.get("grader_id", "")
        self.grader_name = grader_data.get("name", "")
        self.grader_version = grader_data.get("version", "")
        self.grader_binary_hash = grader_data.get("binary_hash", "")
        
        # Parse Constraints
        constraints_data = raw_data.get("execution_constraints", {})
        self.timeout_seconds = int(constraints_data.get("timeout_seconds", 300))
        
        # Parse Extensible Validation Rules
        self.rules: List[ValidationRule] = []
        for r in raw_data.get("validation_rules", []):
            self.rules.append(ValidationRule(r))

class ChallengeParser:
    """Parses and validates the incoming challenge package schema."""
    
    @staticmethod
    def parse(raw_data: Dict[str, Any]) -> ChallengePackage:
        """Validates critical structural fields and builds the ChallengePackage."""
        required_keys = ["session", "assignment", "grader", "validation_rules"]
        for key in required_keys:
            if key not in raw_data:
                raise ValueError(f"Invalid challenge package schema. Missing '{key}' key.")
                
        return ChallengePackage(raw_data)
