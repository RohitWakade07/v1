"""extend sessionstatus enum with lifecycle states

Revision ID: 20260604_extend_sessionstatus_enum
Revises: 20260602_add_results_and_certs
Create Date: 2026-06-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260604_extend_sessionstatus_enum"
down_revision: Union[str, None] = "20260602_add_results_and_certs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New lifecycle states added to SessionStatus in app.models.models
_NEW_SESSION_STATUSES = (
    "CREATED",
    "CHALLENGE_ISSUED",
    "RUNNING",
    "ABORTED",
    "PROOF_GENERATED",
    "PROOF_SUBMITTED",
    "VERIFIED",
    "FAILED",
)


def upgrade() -> None:
    for value in _NEW_SESSION_STATUSES:
        op.execute(
            f"ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS '{value}'"
        )


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely.
    pass
