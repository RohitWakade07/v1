from evaluator.validators.base import BaseValidator
from evaluator.challenge_parser import ValidationRule
from evaluator.validator_registry import ValidatorRegistry

class DirExistsValidator(BaseValidator):
    """Verifies that a specific target directory exists in the filesystem."""
    
    def validate(self, rule: ValidationRule) -> tuple[bool, str, str, int]:
        target = rule.target
        return self.run_bash_script("inspect_filesystem.sh", ["dir_exists", target])

# Automatically register this validator class
ValidatorRegistry.register("dir_exists", DirExistsValidator)
