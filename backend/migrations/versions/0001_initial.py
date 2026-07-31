"""Create initial Qava SQLite schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "questionnaire_drafts",
        sa.Column("draft_id", sa.Text(), nullable=False),
        sa.Column("base_version", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("output_contract_json", sa.Text(), nullable=False),
        sa.Column("output_needs_json", sa.Text(), nullable=False),
        sa.Column("questions_json", sa.Text(), nullable=False),
        sa.Column("health_policy_json", sa.Text(), nullable=False),
        sa.Column("assistance_policy_json", sa.Text(), nullable=False),
        sa.Column("decisions_json", sa.Text(), nullable=False),
        sa.Column("validation_issues_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("draft_id"),
    )
    op.create_index(
        "ix_questionnaire_drafts_updated_at",
        "questionnaire_drafts",
        ["updated_at"],
        unique=False,
    )

    op.create_table(
        "published_questionnaires",
        sa.Column("questionnaire_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("output_contract_json", sa.Text(), nullable=False),
        sa.Column("output_needs_json", sa.Text(), nullable=False),
        sa.Column("questions_json", sa.Text(), nullable=False),
        sa.Column("component_catalog_version", sa.Integer(), nullable=False),
        sa.Column("health_policy_json", sa.Text(), nullable=False),
        sa.Column("assistance_policy_json", sa.Text(), nullable=False),
        sa.Column("allowed_result_adapters_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("published_by", sa.Text(), nullable=False),
        sa.Column("published_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("questionnaire_id", "version"),
    )
    op.create_index(
        "ix_published_questionnaires_questionnaire_id_published_at",
        "published_questionnaires",
        ["questionnaire_id", "published_at"],
        unique=False,
    )

    op.create_table(
        "sessions",
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("questionnaire_id", sa.Text(), nullable=False),
        sa.Column("questionnaire_version", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("active_topic_id", sa.Text(), nullable=True),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column("generated_interactions_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(
        "ix_sessions_questionnaire_id_version",
        "sessions",
        ["questionnaire_id", "questionnaire_version"],
        unique=False,
    )

    op.create_table(
        "interactions",
        sa.Column("interaction_id", sa.Text(), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("session_revision", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("interaction_snapshot_json", sa.Text(), nullable=True),
        sa.Column("submitted_value_json", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("interaction_id"),
    )
    op.create_index(
        "ix_interactions_session_id_created_at",
        "interactions",
        ["session_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "assistance_proposals",
        sa.Column("proposal_id", sa.Text(), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("interaction_id", sa.Text(), nullable=True),
        sa.Column("operation", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("proposal_id"),
    )
    op.create_index(
        "ix_assistance_proposals_session_id_created_at",
        "assistance_proposals",
        ["session_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "publication_attempts",
        sa.Column("publication_id", sa.Text(), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("session_revision", sa.Integer(), nullable=False),
        sa.Column("adapter", sa.Text(), nullable=False),
        sa.Column("destination", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Text(), nullable=False),
        sa.Column("external_reference", sa.Text(), nullable=True),
        sa.Column("error_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("publication_id"),
        sa.UniqueConstraint(
            "session_id",
            "idempotency_key",
            name="uq_publication_attempts_session_idempotency",
        ),
    )
    op.create_index(
        "ix_publication_attempts_session_id_created_at",
        "publication_attempts",
        ["session_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_publication_attempts_session_id_created_at",
        table_name="publication_attempts",
    )
    op.drop_table("publication_attempts")

    op.drop_index(
        "ix_assistance_proposals_session_id_created_at",
        table_name="assistance_proposals",
    )
    op.drop_table("assistance_proposals")

    op.drop_index("ix_interactions_session_id_created_at", table_name="interactions")
    op.drop_table("interactions")

    op.drop_index("ix_sessions_questionnaire_id_version", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index(
        "ix_published_questionnaires_questionnaire_id_published_at",
        table_name="published_questionnaires",
    )
    op.drop_table("published_questionnaires")

    op.drop_index("ix_questionnaire_drafts_updated_at", table_name="questionnaire_drafts")
    op.drop_table("questionnaire_drafts")
