"""add assignment attachment tables

Revision ID: 20260416_000008
Revises: 20260416_000007
Create Date: 2026-04-16 00:00:08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260416_000008"
down_revision = "20260416_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assignment_attachments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("assignment_id", sa.UUID(), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assignment_attachments_assignment_id"), "assignment_attachments", ["assignment_id"], unique=False)

    op.create_table(
        "assignment_submission_attachments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("submission_id", sa.UUID(), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["assignment_submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assignment_submission_attachments_submission_id"),
        "assignment_submission_attachments",
        ["submission_id"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index(op.f("ix_assignment_submission_attachments_submission_id"), table_name="assignment_submission_attachments")
    op.drop_table("assignment_submission_attachments")
    op.drop_index(op.f("ix_assignment_attachments_assignment_id"), table_name="assignment_attachments")
    op.drop_table("assignment_attachments")
