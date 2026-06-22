from alembic import op
import sqlalchemy as sa

revision = 'e3f4g5h6i7j8'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add missing columns
    op.add_column('assignments', sa.Column('submission_filename', sa.String(length=300), nullable=True))
    op.add_column('assignments', sa.Column('submission_instructions', sa.Text(), nullable=True))

    # 2. Add 'week6' to the Postgres ENUM type for AssignmentCategory
    # Using commit=True since ALTER TYPE cannot run inside a transaction block in older postgres (or just raw SQL)
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE assignmentcategory ADD VALUE IF NOT EXISTS 'week6'")

def downgrade():
    op.drop_column('assignments', 'submission_instructions')
    op.drop_column('assignments', 'submission_filename')
    # Postgres doesn't easily allow dropping values from an ENUM type, so we leave 'week6' in place.


