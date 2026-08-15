"""SQLite project repository with a cloud-database-compatible boundary."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.state.project import ProjectState


class SQLiteProjectRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    region TEXT NOT NULL,
                    current_step TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_projects_updated_at "
                "ON projects(updated_at DESC)"
            )

    def save(self, project: ProjectState) -> ProjectState:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (
                    project_id, project_name, industry, region,
                    current_step, updated_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    project_name=excluded.project_name,
                    industry=excluded.industry,
                    region=excluded.region,
                    current_step=excluded.current_step,
                    updated_at=excluded.updated_at,
                    payload_json=excluded.payload_json
                """,
                (
                    project.project_id,
                    project.project_name,
                    project.industry,
                    project.region,
                    project.current_step,
                    project.updated_at.isoformat(),
                    project.model_dump_json(),
                ),
            )
        return project

    def get(self, project_id: str) -> ProjectState | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        return ProjectState.model_validate_json(row["payload_json"]) if row else None

    def list(self, *, limit: int = 100, offset: int = 0) -> list[ProjectState]:
        if limit < 1 or limit > 500 or offset < 0:
            raise ValueError("limit must be 1-500 and offset must be non-negative")
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM projects "
                "ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [ProjectState.model_validate_json(row["payload_json"]) for row in rows]

    def delete(self, project_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM projects WHERE project_id = ?", (project_id,)
            )
        return cursor.rowcount > 0
