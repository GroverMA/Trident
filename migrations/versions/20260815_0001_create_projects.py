"""Create production projects table.

Revision ID: 20260815_0001
Revises:
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260815_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("project_name", sa.String(length=500), nullable=False),
        sa.Column("industry", sa.String(length=300), nullable=False),
        sa.Column("region", sa.String(length=300), nullable=False),
        sa.Column("current_step", sa.String(length=100), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("project_id"),
    )
    op.create_index(
        "ix_projects_updated_at", "projects", ["updated_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_projects_updated_at", table_name="projects")
    op.drop_table("projects")
