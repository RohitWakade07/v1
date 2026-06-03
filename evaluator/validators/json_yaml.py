from evaluator.validators.base import BaseValidator
from evaluator.challenge_parser import ValidationRule
from evaluator.validator_registry import ValidatorRegistry

class JsonYamlValidator(BaseValidator):
    """Verifies that a JSON or YAML file has valid syntax structure."""
    
    def validate(self, rule: ValidationRule) -> tuple[bool, str, str, int]:
        target = rule.target
        format_type = rule.metadata.get("format", "json")
        return self.run_bash_script("inspect_filesystem.sh", ["check_json_yaml", target, format_type])

# Automatically register this validator class
ValidatorRegistry.register("json_yaml", JsonYamlValidator)
