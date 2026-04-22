"""add comment replies

Revision ID: 20260411_000004
Revises: 20260411_000003
Create Date: 2026-04-11 22:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260411_000004"
down_revision = "20260411_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("comments", sa.Column("parent_comment_id", sa.Uuid(), nullable=True))
    op.create_index("ix_comments_parent_comment_id", "comments", ["parent_comment_id"], unique=False)
    op.create_foreign_key(
        "fk_comments_parent_comment_id_comments",
        "comments",
        "comments",
        ["parent_comment_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_comments_parent_comment_id_comments", "comments", type_="foreignkey")
    op.drop_index("ix_comments_parent_comment_id", table_name="comments")
    op.drop_column("comments", "parent_comment_id")
