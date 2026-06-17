"""feature_expansion_quiz_announcements_notifications_auth_assignments

Revision ID: c1a2b3d4e5f6
Revises: 1b0957bede17
Create Date: 2026-06-17 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, None] = '1b0957bede17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enum_if_not_exists(op, name: str, values: list):
    """Idempotent enum type creation using PL/pgSQL."""
    vals = ", ".join(f"'{v}'" for v in values)
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
                CREATE TYPE {name} AS ENUM ({vals});
            END IF;
        END
        $$;
    """)


def upgrade() -> None:
    # ── 1. Quiz tables ────────────────────────────────────────────────
    _create_enum_if_not_exists(op, 'questiontype', ['single', 'multiple'])

    op.create_table(
        'quizzes',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assignment_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('marks_per_question', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', name='uq_quiz_per_assignment'),
    )
    op.create_index('ix_quizzes_id', 'quizzes', ['id'])
    op.create_index('ix_quizzes_assignment_id', 'quizzes', ['assignment_id'])

    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('quiz_id', sa.UUID(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False, server_default='single'),
        sa.Column('marks', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_quiz_questions_id', 'quiz_questions', ['id'])
    op.create_index('ix_quiz_questions_quiz_id', 'quiz_questions', ['quiz_id'])

    op.create_table(
        'quiz_options',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_quiz_options_id', 'quiz_options', ['id'])
    op.create_index('ix_quiz_options_question_id', 'quiz_options', ['question_id'])

    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('quiz_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('total_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quiz_id', 'student_id', name='uq_one_attempt_per_student'),
    )
    op.create_index('ix_quiz_attempts_id', 'quiz_attempts', ['id'])
    op.create_index('ix_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'])
    op.create_index('ix_quiz_attempts_student_id', 'quiz_attempts', ['student_id'])

    op.create_table(
        'quiz_answers',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('attempt_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('marks_awarded', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['attempt_id'], ['quiz_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_quiz_answers_id', 'quiz_answers', ['id'])
    op.create_index('ix_quiz_answers_attempt_id', 'quiz_answers', ['attempt_id'])

    op.create_table(
        'quiz_answer_options',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('answer_id', sa.UUID(), nullable=False),
        sa.Column('option_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['quiz_answers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['option_id'], ['quiz_options.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── 2. Announcement tables ────────────────────────────────────────
    _create_enum_if_not_exists(op, 'audiencetype', ['students', 'mentors', 'all'])

    op.create_table(
        'announcements',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('admin_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('audience', sa.String(20), nullable=False, server_default='all'),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['admin_id'], ['mentors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_announcements_id', 'announcements', ['id'])

    op.create_table(
        'announcement_reads',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('announcement_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('read_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['announcement_id'], ['announcements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('announcement_id', 'user_id', name='uq_announcement_read'),
    )

    # ── 3. Replace notifications table ───────────────────────────────
    op.drop_table('notifications')
    _create_enum_if_not_exists(op, 'recipienttype', ['student', 'mentor'])
    _create_enum_if_not_exists(op, 'notificationsourcetype', ['announcement', 'submission', 'quiz', 'system'])

    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('recipient_id', sa.UUID(), nullable=False),
        sa.Column('recipient_type', sa.String(20), nullable=False),
        sa.Column('source_type', sa.String(20), nullable=False, server_default='system'),
        sa.Column('source_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'])
    op.create_index('ix_notifications_recipient_id', 'notifications', ['recipient_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])

    # ── 4. Auth fields ────────────────────────────────────────────────
    op.add_column('students', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('students', sa.Column('locked_until', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('students', sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('students', sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='false'))

    op.add_column('mentors', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('mentors', sa.Column('locked_until', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('mentors', sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True))

    # ── 5. Assignment extensions ──────────────────────────────────────
    op.add_column('assignments', sa.Column('resource_links', postgresql.JSONB(), nullable=False, server_default='[]'))
    op.add_column('assignments', sa.Column('late_penalty_pct', sa.Float(), nullable=False, server_default='0.0'))

    # ── 6. Submission rate limit table ────────────────────────────────
    op.create_table(
        'submission_rate_limits',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('assignment_id', sa.UUID(), nullable=False),
        sa.Column('last_submitted_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'assignment_id', name='uq_rate_limit_student_assignment'),
    )


def downgrade() -> None:
    op.drop_table('submission_rate_limits')
    op.drop_column('assignments', 'late_penalty_pct')
    op.drop_column('assignments', 'resource_links')
    op.drop_column('mentors', 'last_login_at')
    op.drop_column('mentors', 'locked_until')
    op.drop_column('mentors', 'failed_login_attempts')
    op.drop_column('students', 'must_change_password')
    op.drop_column('students', 'last_login_at')
    op.drop_column('students', 'locked_until')
    op.drop_column('students', 'failed_login_attempts')
    op.drop_table('notifications')
    # Recreate old notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('mentor_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['mentor_id'], ['mentors.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.drop_table('announcement_reads')
    op.drop_table('announcements')
    op.drop_table('quiz_answer_options')
    op.drop_table('quiz_answers')
    op.drop_table('quiz_attempts')
    op.drop_table('quiz_options')
    op.drop_table('quiz_questions')
    op.drop_table('quizzes')
    op.execute("DROP TYPE IF EXISTS questiontype")
    op.execute("DROP TYPE IF EXISTS audiencetype")
    op.execute("DROP TYPE IF EXISTS recipienttype")
    op.execute("DROP TYPE IF EXISTS notificationsourcetype")
