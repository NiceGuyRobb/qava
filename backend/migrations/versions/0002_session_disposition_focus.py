"""Add skip_dispositions_json and navigation_focus_json to sessions.

Revision ID: 0002_session_disposition_focus
Revises: 0001_initial
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_session_disposition_focus"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "skip_dispositions_json",
                sa.Text(),
                nullable=False,
                server_default="{}",
            )
        )
        batch_op.add_column(
            sa.Column(
                "navigation_focus_json",
                sa.Text(),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_column("navigation_focus_json")
        batch_op.drop_column("skip_dispositions_json")
