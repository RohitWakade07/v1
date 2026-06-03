from evaluator.validators.base import BaseValidator
from evaluator.challenge_parser import ValidationRule
from evaluator.validator_registry import ValidatorRegistry

class PermissionValidator(BaseValidator):
    """Verifies that a target file or folder has correct octal permissions."""
    
    def validate(self, rule: ValidationRule) -> tuple[bool, str, str, int]:
        target = rule.target
        expected_perm = str(rule.metadata.get("permissions", "644"))
        return self.run_bash_script("inspect_filesystem.sh", ["check_permission", target, expected_perm])

# Automatically register this validator class
ValidatorRegistry.register("permission", PermissionValidator)
