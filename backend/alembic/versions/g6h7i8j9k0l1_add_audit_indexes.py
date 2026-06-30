"""Add audit indexes for FK columns and query filters

Revision ID: g6h7i8j9k0l1
Revises: f4g5h6i7j8k9
Create Date: 2026-06-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "g6h7i8j9k0l1"
down_revision: Union[str, None] = "f4g5h6i7j8k9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_assignments_created_by_id",
        "assignments",
        ["created_by_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_submissions_status",
        "submissions",
        ["status"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_classroom_enrollments_status",
        "classroom_enrollments",
        ["status"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_notifications_recipient_id_is_read",
        "notifications",
        ["recipient_id", "is_read"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_grading_sessions_status",
        "grading_sessions",
        ["status"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_quiz_answers_question_id",
        "quiz_answers",
        ["question_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_quiz_answer_options_answer_id",
        "quiz_answer_options",
        ["answer_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_quiz_answer_options_option_id",
        "quiz_answer_options",
        ["option_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_quiz_answer_options_option_id", table_name="quiz_answer_options")
    op.drop_index("ix_quiz_answer_options_answer_id", table_name="quiz_answer_options")
    op.drop_index("ix_quiz_answers_question_id", table_name="quiz_answers")
    op.drop_index("ix_grading_sessions_status", table_name="grading_sessions")
    op.drop_index("ix_notifications_recipient_id_is_read", table_name="notifications")
    op.drop_index("ix_classroom_enrollments_status", table_name="classroom_enrollments")
    op.drop_index("ix_submissions_status", table_name="submissions")
    op.drop_index("ix_assignments_created_by_id", table_name="assignments")
