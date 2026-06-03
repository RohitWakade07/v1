"""add results and certs

Revision ID: 20260602_add_results_and_certs
Revises: None
Create Date: 2026-06-02 10:25:09.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260602_add_results_and_certs'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create final_results ──────────────────────────────────────────
    op.create_table(
        'final_results',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('session_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('student_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('assignment_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('score_breakdown', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['grading_sessions.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id']),
    )
    op.create_index(op.f('ix_final_results_id'), 'final_results', ['id'], unique=False)
    op.create_index(op.f('ix_final_results_session_id'), 'final_results', ['session_id'], unique=False)
    op.create_index(op.f('ix_final_results_student_id'), 'final_results', ['student_id'], unique=False)
    op.create_index(op.f('ix_final_results_assignment_id'), 'final_results', ['assignment_id'], unique=False)

    # ── Create certificates ───────────────────────────────────────────
    op.create_table(
        'certificates',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('student_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('assignment_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('final_result_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('certificate_code', sa.String(length=100), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id']),
        sa.ForeignKeyConstraint(['final_result_id'], ['final_results.id']),
    )
    op.create_index(op.f('ix_certificates_id'), 'certificates', ['id'], unique=False)
    op.create_index(op.f('ix_certificates_student_id'), 'certificates', ['student_id'], unique=False)
    op.create_index(op.f('ix_certificates_assignment_id'), 'certificates', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_certificates_final_result_id'), 'certificates', ['final_result_id'], unique=False)
    op.create_index(op.f('ix_certificates_certificate_code'), 'certificates', ['certificate_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_certificates_certificate_code'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_final_result_id'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_assignment_id'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_student_id'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_id'), table_name='certificates')
    op.drop_table('certificates')

    op.drop_index(op.f('ix_final_results_assignment_id'), table_name='final_results')
    op.drop_index(op.f('ix_final_results_student_id'), table_name='final_results')
    op.drop_index(op.f('ix_final_results_session_id'), table_name='final_results')
    op.drop_index(op.f('ix_final_results_id'), table_name='final_results')
    op.drop_table('final_results')
