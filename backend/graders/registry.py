import importlib
import importlib.util
import sys
from pathlib import Path
from graders.base_grader import BaseGrader

def get_grader(assignment_id: str) -> type[BaseGrader]:
    valid_slugs = ["week1", "week2", "week3", "week4", "week5", "week6", "week7", "week8", "week9", "week10", "week11", "week12"]
    if assignment_id not in valid_slugs:
        raise ValueError(
            f"No grader registered for assignment_id='{assignment_id}'. "
            f"Available: {valid_slugs}"
        )
    
    module_name = f"graders.{assignment_id}.grader"
    
    # Force reload if it's already in sys.modules
    if module_name in sys.modules:
        module = sys.modules[module_name]
        importlib.reload(module)
    else:
        module = importlib.import_module(module_name)
    
    # We assume the class name follows a specific format like Week1Grader, Week4Grader, etc.
    class_name = f"{assignment_id.capitalize()}Grader"
    grader_class = getattr(module, class_name)
    
    return grader_class

