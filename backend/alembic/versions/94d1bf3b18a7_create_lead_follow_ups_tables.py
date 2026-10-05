"""create lead follow ups tables

Revision ID: 94d1bf3b18a7
Revises: d4f8a1c2b3e4
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "94d1bf3b18a7"
down_revision: Union[str, Sequence[str], None] = "d4f8a1c2b3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lead_follow_ups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "idempotency_key",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'CANCELLED')",
            name="ck_lead_follow_ups_status",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_lead_follow_ups_attempt_count",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idempotency_key",
            name="uq_lead_follow_ups_idempotency_key",
        ),
    )

    op.create_index(
        "ix_lead_follow_ups_lead_id",
        "lead_follow_ups",
        ["lead_id"],
    )
    op.create_index(
        "ix_lead_follow_ups_appointment_id",
        "lead_follow_ups",
        ["appointment_id"],
    )
    op.create_index(
        "ix_lead_follow_ups_status_scheduled_at",
        "lead_follow_ups",
        ["status", "scheduled_at"],
    )

    op.create_table(
        "lead_follow_up_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("follow_up_id", sa.Integer(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column(
            "channel",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["follow_up_id"],
            ["lead_follow_ups.id"],
        ),
        sa.CheckConstraint(
            "attempt_number >= 1",
            name="ck_lead_follow_up_attempts_number",
        ),
        sa.CheckConstraint(
            "channel IN ('MANUAL', 'EMAIL', 'WHATSAPP')",
            name="ck_lead_follow_up_attempts_channel",
        ),
        sa.CheckConstraint(
            "status IN ('SUCCESS', 'FAILED')",
            name="ck_lead_follow_up_attempts_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "follow_up_id",
            "attempt_number",
            name="uq_lead_follow_up_attempts_number",
        ),
    )

    op.create_index(
        "ix_lead_follow_up_attempts_follow_up_id",
        "lead_follow_up_attempts",
        ["follow_up_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_lead_follow_up_attempts_follow_up_id",
        table_name="lead_follow_up_attempts",
    )
    op.drop_table("lead_follow_up_attempts")

    op.drop_index(
        "ix_lead_follow_ups_status_scheduled_at",
        table_name="lead_follow_ups",
    )
    op.drop_index(
        "ix_lead_follow_ups_appointment_id",
        table_name="lead_follow_ups",
    )
    op.drop_index(
        "ix_lead_follow_ups_lead_id",
        table_name="lead_follow_ups",
    )
    op.drop_table("lead_follow_ups")