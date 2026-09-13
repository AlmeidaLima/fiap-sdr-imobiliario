"""add property external id

Revision ID: ba7235f16efa
Revises: 88433f05b0e8
Create Date: 2026-09-13 17:55:12.368243

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ba7235f16efa"
down_revision: Union[str, Sequence[str], None] = "88433f05b0e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "properties",
        sa.Column(
            "external_id",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_properties_external_id"),
        "properties",
        ["external_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_properties_external_id"),
        table_name="properties",
    )

    op.drop_column(
        "properties",
        "external_id",
    )