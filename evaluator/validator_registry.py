from typing import Dict, Type, Any
from evaluator.evaluator_logging import logger

class ValidatorRegistry:
    """Registry maintaining rules to validator plugin class mappings."""
    
    _registry: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, type_name: str, validator_class: Type[Any]) -> None:
        """Registers a new validator plugin class associated with a specific type rule."""
        cls._registry[type_name] = validator_class
        logger.info(f"Registered validator plugin: '{type_name}' -> {validator_class.__name__}")

    @classmethod
    def get_validator(cls, type_name: str) -> Type[Any]:
        """Fetches the registered validator class. Returns None if unregistered."""
        return cls._registry.get(type_name)
