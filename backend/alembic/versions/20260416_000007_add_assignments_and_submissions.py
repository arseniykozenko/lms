"""add assignments and submissions

Revision ID: 20260416_000007
Revises: 20260415_000006
Create Date: 2026-04-16 00:00:07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260416_000007"
down_revision = "20260415_000006"
branch_labels = None
depends_on = None


submission_status = postgresql.ENUM("draft", "submitted", "graded", name="submission_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    submission_status.create(bind, checkfirst=True)

    op.create_table(
        "assignments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("module_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("instructions_markdown", sa.Text(), nullable=False),
        sa.Column("attachment_url", sa.String(length=500), nullable=True),
        sa.Column("attachment_name", sa.String(length=255), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assignments_module_id"), "assignments", ["module_id"], unique=False)

    op.create_table(
        "assignment_submissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("assignment_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("answer_markdown", sa.Text(), nullable=True),
        sa.Column("attachment_url", sa.String(length=500), nullable=True),
        sa.Column("attachment_name", sa.String(length=255), nullable=True),
        sa.Column("status", submission_status, nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("feedback_markdown", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assignment_submissions_assignment_id"), "assignment_submissions", ["assignment_id"], unique=False)
    op.create_index(op.f("ix_assignment_submissions_student_id"), "assignment_submissions", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_assignment_submissions_student_id"), table_name="assignment_submissions")
    op.drop_index(op.f("ix_assignment_submissions_assignment_id"), table_name="assignment_submissions")
    op.drop_table("assignment_submissions")
    op.drop_index(op.f("ix_assignments_module_id"), table_name="assignments")
    op.drop_table("assignments")
    bind = op.get_bind()
    submission_status.drop(bind, checkfirst=True)
