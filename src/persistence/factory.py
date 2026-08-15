"""Environment-aware repository selection with production-safe defaults."""

from __future__ import annotations

import os
from pathlib import Path

from src.persistence.postgres_projects import PostgresProjectRepository
from src.persistence.projects import ProjectRepository
from src.persistence.sqlite_projects import SQLiteProjectRepository


class PersistenceConfigurationError(RuntimeError):
    pass


def create_project_repository() -> ProjectRepository:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise PersistenceConfigurationError(
                "DATABASE_URL must be a PostgreSQL connection string"
            )
        return PostgresProjectRepository(database_url)

    if os.getenv("TRIDENT_ALLOW_SQLITE", "").lower() not in {"1", "true", "yes"}:
        raise PersistenceConfigurationError(
            "DATABASE_URL is required. SQLite is available only when "
            "TRIDENT_ALLOW_SQLITE=true is explicitly set for local development."
        )

    path = Path(os.getenv("TRIDENT_DATABASE_PATH", "data/trident.db")).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteProjectRepository(path)
