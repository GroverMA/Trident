from __future__ import annotations

import pytest

from scripts.start_api import (
    deployment_environment,
    should_run_migrations,
    uvicorn_command,
)


def test_local_startup_does_not_require_cloud_database(monkeypatch) -> None:
    monkeypatch.delenv("TRIDENT_ENV", raising=False)
    assert deployment_environment() == "development"
    assert should_run_migrations("development", "") is False


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_customer_environments_require_database_url(environment: str) -> None:
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        should_run_migrations(environment, "")


def test_production_sqlite_demo_skips_migrations() -> None:
    assert should_run_migrations("production", "", "sqlite") is False


def test_sqlite_mode_rejects_database_url() -> None:
    with pytest.raises(RuntimeError, match="Remove DATABASE_URL"):
        should_run_migrations(
            "production", "postgresql://example.invalid/trident", "sqlite"
        )


def test_database_url_mode_requires_database_url() -> None:
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        should_run_migrations("production", "", "database_url")


def test_postgres_startup_runs_migrations() -> None:
    assert should_run_migrations(
        "production", "postgresql://example.invalid/trident"
    ) is True


def test_uvicorn_command_uses_host_port_and_worker_settings(monkeypatch) -> None:
    monkeypatch.delenv("TRIDENT_DATABASE_MODE", raising=False)
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("WEB_CONCURRENCY", "2")
    command = uvicorn_command()
    assert command[command.index("--port") + 1] == "9000"
    assert command[command.index("--workers") + 1] == "2"


def test_sqlite_mode_rejects_multiple_api_workers(monkeypatch) -> None:
    monkeypatch.setenv("TRIDENT_DATABASE_MODE", "sqlite")
    monkeypatch.setenv("WEB_CONCURRENCY", "2")

    with pytest.raises(RuntimeError, match="must be 1"):
        uvicorn_command()
