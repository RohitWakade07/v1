"""fix_questiontype_column_to_varchar

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3d4e5f6
Create Date: 2026-06-17 18:30:00.000000

If the quiz_questions.type column was created as a PostgreSQL ENUM (questiontype)
instead of VARCHAR, this migration converts it to VARCHAR(20) so plain string
values like 'single' and 'multiple' can be stored without enum serialization issues.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotently convert quiz_questions.type from ENUM to VARCHAR if needed.
    # This is safe to run even if the column is already VARCHAR.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'quiz_questions'
                  AND column_name = 'type'
                  AND udt_name = 'questiontype'
            ) THEN
                ALTER TABLE quiz_questions
                    ALTER COLUMN type TYPE VARCHAR(20) USING type::text;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    # No-op: we intentionally keep VARCHAR — reverting to ENUM causes the same bug.
    pass
