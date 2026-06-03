from evaluator.validators.base import BaseValidator
from evaluator.challenge_parser import ValidationRule
from evaluator.validator_registry import ValidatorRegistry

class ContentValidator(BaseValidator):
    """Verifies that a file contains specific regex patterns or keywords."""
    
    def validate(self, rule: ValidationRule) -> tuple[bool, str, str, int]:
        target = rule.target
        pattern = rule.metadata.get("pattern", "")
        return self.run_bash_script("inspect_filesystem.sh", ["check_content", target, pattern])

# Automatically register this validator class
ValidatorRegistry.register("content", ContentValidator)
