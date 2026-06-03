from evaluator.validators.base import BaseValidator
from evaluator.challenge_parser import ValidationRule
from evaluator.validator_registry import ValidatorRegistry

class FileExistsValidator(BaseValidator):
    """Verifies that a specific target file exists in the filesystem."""
    
    def validate(self, rule: ValidationRule) -> tuple[bool, str, str, int]:
        target = rule.target
        return self.run_bash_script("inspect_filesystem.sh", ["file_exists", target])

# Automatically register this validator class
ValidatorRegistry.register("file_exists", FileExistsValidator)
