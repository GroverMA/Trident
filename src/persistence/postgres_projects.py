"""Production PostgreSQL project repository (Neon-compatible)."""

from __future__ import annotations

from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

from src.persistence.schema import projects_table
from src.state.project import ProjectState


class PostgresProjectRepository:
    """Persist projects in PostgreSQL using a small, replaceable adapter."""

    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        if not database_url.startswith(
            ("postgres://", "postgresql://", "postgresql+psycopg://")
        ):
            raise ValueError("PostgresProjectRepository requires a PostgreSQL URL")
        normalized = database_url
        if normalized.startswith("postgres://"):
            normalized = normalized.replace("postgres://", "postgresql+psycopg://", 1)
        elif normalized.startswith("postgresql://"):
            normalized = normalized.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        self.engine = engine or create_engine(
            normalized,
            pool_pre_ping=True,
            pool_use_lifo=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=5,
        )

    def ping(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1")).scalar_one()

    def save(self, project: ProjectState) -> ProjectState:
        values = {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "industry": project.industry,
            "region": project.region,
            "current_step": project.current_step,
            "updated_at": project.updated_at,
            "payload_json": project.model_dump(mode="json"),
        }
        statement = insert(projects_table).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[projects_table.c.project_id],
            set_={key: value for key, value in values.items() if key != "project_id"},
        )
        with self.engine.begin() as connection:
            connection.execute(statement)
        return project

    def get(self, project_id: str) -> ProjectState | None:
        with self.engine.connect() as connection:
            payload = connection.execute(
                select(projects_table.c.payload_json).where(
                    projects_table.c.project_id == project_id
                )
            ).scalar_one_or_none()
        return ProjectState.model_validate(payload) if payload else None

    def list(self, *, limit: int = 100, offset: int = 0) -> list[ProjectState]:
        if limit < 1 or limit > 500 or offset < 0:
            raise ValueError("limit must be 1-500 and offset must be non-negative")
        statement = (
            select(projects_table.c.payload_json)
            .order_by(projects_table.c.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        with self.engine.connect() as connection:
            payloads = connection.execute(statement).scalars().all()
        return [ProjectState.model_validate(payload) for payload in payloads]

    def delete(self, project_id: str) -> bool:
        with self.engine.begin() as connection:
            result = connection.execute(
                delete(projects_table).where(projects_table.c.project_id == project_id)
            )
        return bool(result.rowcount)
