from graders.week1.grader import Week1Grader
from graders.week2.grader import Week2Grader
from graders.week3.grader import Week3Grader
from graders.week4.grader import Week4Grader
from graders.week5.grader import Week5Grader
from graders.week6.grader import Week6Grader
from graders.week7.grader import Week7Grader
from graders.week8.grader import Week8Grader
from graders.week9.grader import Week9Grader
from graders.base_grader import BaseGrader

GRADER_REGISTRY: dict[str, type[BaseGrader]] = {
    "week1": Week1Grader,
    "week2": Week2Grader,
    "week3": Week3Grader,
    "week4": Week4Grader,
    "week5": Week5Grader,
    "week6": Week6Grader,
    "week7": Week7Grader,
    "week8": Week8Grader,
    "week9": Week9Grader,
}


def get_grader(assignment_id: str) -> type[BaseGrader]:
    grader_class = GRADER_REGISTRY.get(assignment_id)
    if grader_class is None:
        raise ValueError(
            f"No grader registered for assignment_id='{assignment_id}'. "
            f"Available: {list(GRADER_REGISTRY.keys())}"
        )
    return grader_class
