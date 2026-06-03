from evaluator.validators.base import BaseValidator
from evaluator.challenge_parser import ValidationRule
from evaluator.validator_registry import ValidatorRegistry

class ExtensionValidator(BaseValidator):
    """Verifies that a file's suffix matches the expected file format extension."""
    
    def validate(self, rule: ValidationRule) -> tuple[bool, str, str, int]:
        target = rule.target
        expected_ext = rule.metadata.get("extension", "")
        return self.run_bash_script("inspect_filesystem.sh", ["check_extension", target, expected_ext])

# Automatically register this validator class
ValidatorRegistry.register("extension", ExtensionValidator)
