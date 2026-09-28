"""create appointments table

Revision ID: d4f8a1c2b3e4
Revises: c5a6d252b998
Create Date: 2026-09-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4f8a1c2b3e4"
down_revision: Union[str, Sequence[str], None] = "c5a6d252b998"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=True),
        sa.Column("appointment_type", sa.String(length=20), nullable=False),
        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.CheckConstraint(
            "appointment_type IN ('VISITA', 'REUNIAO')",
            name="ck_appointments_type",
        ),
        sa.CheckConstraint(
            "status IN ('CONFIRMED', 'CANCELLED')",
            name="ck_appointments_status",
        ),
        sa.CheckConstraint(
            "appointment_type != 'VISITA' OR property_id IS NOT NULL",
            name="ck_appointments_visit_property",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idempotency_key",
            name="uq_appointments_idempotency_key",
        ),
    )
    op.create_index(
        "ix_appointments_lead_id",
        "appointments",
        ["lead_id"],
    )
    op.create_index(
        "ix_appointments_property_id",
        "appointments",
        ["property_id"],
    )
    op.create_index(
        "ix_appointments_scheduled_at",
        "appointments",
        ["scheduled_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_scheduled_at", table_name="appointments")
    op.drop_index("ix_appointments_property_id", table_name="appointments")
    op.drop_index("ix_appointments_lead_id", table_name="appointments")
    op.drop_table("appointments")
