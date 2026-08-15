"""Persistence adapters for project state."""

from src.persistence.projects import ProjectRepository
from src.persistence.sqlite_projects import SQLiteProjectRepository

__all__ = ["ProjectRepository", "SQLiteProjectRepository"]
