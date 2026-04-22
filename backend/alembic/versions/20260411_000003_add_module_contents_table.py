"""add module contents table

Revision ID: 20260411_000003
Revises: 20260410_000002
Create Date: 2026-04-11 18:40:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260411_000003"
down_revision = "20260410_000002"
branch_labels = None
depends_on = None


module_content_type = postgresql.ENUM("text", "video", "pdf", "link", name="module_content_type", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    module_content_type.create(bind, checkfirst=True)

    op.create_table(
        "module_contents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("module_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_type", module_content_type, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("asset_url", sa.String(length=500), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_module_contents_module_id"), "module_contents", ["module_id"], unique=False)
    op.create_index(op.f("ix_module_contents_content_type"), "module_contents", ["content_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_module_contents_content_type"), table_name="module_contents")
    op.drop_index(op.f("ix_module_contents_module_id"), table_name="module_contents")
    op.drop_table("module_contents")
    bind = op.get_bind()
    module_content_type.drop(bind, checkfirst=True)
