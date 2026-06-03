from evaluator.validators.base import BaseValidator
from evaluator.challenge_parser import ValidationRule
from evaluator.validator_registry import ValidatorRegistry

class SizeValidator(BaseValidator):
    """Verifies that a file's size is within specified minimum/maximum ranges."""
    
    def validate(self, rule: ValidationRule) -> tuple[bool, str, str, int]:
        target = rule.target
        min_size = str(rule.metadata.get("min_bytes", ""))
        max_size = str(rule.metadata.get("max_bytes", ""))
        return self.run_bash_script("inspect_filesystem.sh", ["check_size", target, min_size, max_size])

# Automatically register this validator class
ValidatorRegistry.register("size", SizeValidator)
