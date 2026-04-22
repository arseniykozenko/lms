"""add presentation module content type

Revision ID: 20260415_000006
Revises: 20260415_000005
Create Date: 2026-04-15 00:00:06
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260415_000006"
down_revision: str | Sequence[str] | None = "20260415_000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE module_content_type ADD VALUE IF NOT EXISTS 'presentation'")


def downgrade() -> None:
    # PostgreSQL enum values are not removed in downgrade to avoid unsafe type rewrites.
    pass
