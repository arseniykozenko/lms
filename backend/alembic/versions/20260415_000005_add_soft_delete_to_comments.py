"""add soft delete to comments

Revision ID: 20260415_000005
Revises: 20260411_000004
Create Date: 2026-04-15 00:00:05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260415_000005"
down_revision: str | Sequence[str] | None = "20260411_000004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("comments", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("comments", "is_deleted", server_default=None)


def downgrade() -> None:
    op.drop_column("comments", "is_deleted")
