"""add WEB follow-up channel

Revision ID: a61f8c2d4e90
Revises: 94d1bf3b18a7
Create Date: 2026-10-05
"""

from typing import Sequence, Union

from alembic import op


revision: str = "a61f8c2d4e90"
down_revision: Union[str, Sequence[str], None] = "94d1bf3b18a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_lead_follow_up_attempts_channel",
        "lead_follow_up_attempts",
        type_="check",
    )
    op.create_check_constraint(
        "ck_lead_follow_up_attempts_channel",
        "lead_follow_up_attempts",
        "channel IN ('MANUAL', 'EMAIL', 'WHATSAPP', 'WEB')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_lead_follow_up_attempts_channel",
        "lead_follow_up_attempts",
        type_="check",
    )
    op.create_check_constraint(
        "ck_lead_follow_up_attempts_channel",
        "lead_follow_up_attempts",
        "channel IN ('MANUAL', 'EMAIL', 'WHATSAPP')",
    )
