from graders.base_grader import GradingResult
from app.core.config import settings


async def generate_ai_feedback(
    result: GradingResult,
    assignment_title: str,
) -> str:
    """
    Future implementation. Currently returns empty string.
    When ENABLE_AI_FEEDBACK=True, will call Anthropic API.
    """
    if not settings.ENABLE_AI_FEEDBACK:
        return ""
    # TODO: implement when flag is enabled
    return ""
