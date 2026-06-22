"""Add max_attempts to Quiz and attempt_number to QuizAttempt

Revision ID: 03318072fc7d
Revises: e3f4g5h6i7j8
Create Date: 2026-06-22 09:57:29.382002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03318072fc7d'
down_revision: Union[str, None] = 'e3f4g5h6i7j8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add max_attempts to quizzes
    op.add_column('quizzes', sa.Column('max_attempts', sa.Integer(), server_default='1', nullable=False))
    
    # Add attempt_number to quiz_attempts
    op.add_column('quiz_attempts', sa.Column('attempt_number', sa.Integer(), server_default='1', nullable=False))
    
    # Update UniqueConstraint
    op.drop_constraint('uq_one_attempt_per_student', 'quiz_attempts', type_='unique')
    op.create_unique_constraint('uq_attempt_per_student', 'quiz_attempts', ['quiz_id', 'student_id', 'attempt_number'])


def downgrade() -> None:
    op.drop_constraint('uq_attempt_per_student', 'quiz_attempts', type_='unique')
    op.create_unique_constraint('uq_one_attempt_per_student', 'quiz_attempts', ['quiz_id', 'student_id'])
    op.drop_column('quiz_attempts', 'attempt_number')
    op.drop_column('quizzes', 'max_attempts')
