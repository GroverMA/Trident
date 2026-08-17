"""Environment-aware repository selection with production-safe defaults."""

from __future__ import annotations

import os
from pathlib import Path

from src.persistence.postgres_projects import PostgresProjectRepository
from src.persistence.mysql_projects import MySQLProjectRepository
from src.persistence.projects import ProjectRepository
from src.persistence.sqlite_projects import SQLiteProjectRepository


class PersistenceConfigurationError(RuntimeError):
    pass


def create_project_repository() -> ProjectRepository:
    environment = os.getenv("TRIDENT_ENV", "development").strip().lower()
    allowed_environments = {"development", "test", "staging", "production"}
    if environment not in allowed_environments:
        raise PersistenceConfigurationError(
            "TRIDENT_ENV must be development, test, staging, or production"
        )

    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        if database_url.startswith(
            ("postgres://", "postgresql://", "postgresql+psycopg://")
        ):
            return PostgresProjectRepository(database_url)
        if database_url.startswith(("mysql://", "mysql+pymysql://")):
            return MySQLProjectRepository(database_url)
        raise PersistenceConfigurationError(
            "DATABASE_URL must be a PostgreSQL or MySQL connection string"
        )

    if environment in {"staging", "production"}:
        raise PersistenceConfigurationError(
            f"DATABASE_URL is required when TRIDENT_ENV={environment}; "
            "production-like environments never fall back to SQLite"
        )

    # Local development and automated tests must remain runnable without cloud
    # credentials. This database is intentionally isolated from customer data.
    path = Path(os.getenv("TRIDENT_DATABASE_PATH", "data/trident.db")).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteProjectRepository(path)
