"""Database schema shared by production adapters and migrations."""

from sqlalchemy import JSON, Column, DateTime, MetaData, String, Table
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

projects_table = Table(
    "projects",
    metadata,
    Column("project_id", String(64), primary_key=True),
    Column("project_name", String(500), nullable=False),
    Column("industry", String(300), nullable=False),
    Column("region", String(300), nullable=False),
    Column("current_step", String(100), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, index=True),
    Column("payload_json", JSON().with_variant(JSONB, "postgresql"), nullable=False),
)
