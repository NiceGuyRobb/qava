"""Add published_artifacts store for output-adapter publications.

Revision ID: 0003_published_artifacts
Revises: 0002_session_disposition_focus
Create Date: 2026-07-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_published_artifacts"
down_revision = "0002_session_disposition_focus"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "published_artifacts",
        sa.Column("publication_id", sa.Text(), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("session_revision", sa.Integer(), nullable=False),
        sa.Column("adapter", sa.Text(), nullable=False),
        sa.Column("destination", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("document_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("publication_id"),
    )
    op.create_index(
        "ix_published_artifacts_session_id",
        "published_artifacts",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_published_artifacts_session_id", table_name="published_artifacts")
    op.drop_table("published_artifacts")
