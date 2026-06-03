from evaluator.validators.base import BaseValidator
from evaluator.challenge_parser import ValidationRule
from evaluator.validator_registry import ValidatorRegistry

class ArchiveValidator(BaseValidator):
    """Verifies that an archive is uncorrupted and contains specified files."""
    
    def validate(self, rule: ValidationRule) -> tuple[bool, str, str, int]:
        target = rule.target
        format_type = rule.metadata.get("format", "zip")
        contains_file = rule.metadata.get("contains_file", "")
        return self.run_bash_script("inspect_filesystem.sh", ["check_archive", target, format_type, contains_file])

# Automatically register this validator class
ValidatorRegistry.register("archive", ArchiveValidator)
