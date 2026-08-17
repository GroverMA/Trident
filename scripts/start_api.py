"""Start the API with deployment-safe database preparation."""

from __future__ import annotations

import os
import subprocess
import sys


PRODUCTION_ENVIRONMENTS = {"staging", "production"}
ALLOWED_ENVIRONMENTS = {"development", "test", *PRODUCTION_ENVIRONMENTS}


def deployment_environment() -> str:
    environment = os.getenv("TRIDENT_ENV", "development").strip().lower()
    if environment not in ALLOWED_ENVIRONMENTS:
        allowed = ", ".join(sorted(ALLOWED_ENVIRONMENTS))
        raise RuntimeError(f"TRIDENT_ENV must be one of: {allowed}")
    return environment


def should_run_migrations(
    environment: str, database_url: str, database_mode: str = ""
) -> bool:
    database_mode = database_mode.strip().lower()
    if database_mode == "sqlite":
        if database_url:
            raise RuntimeError("Remove DATABASE_URL when TRIDENT_DATABASE_MODE=sqlite")
        return False
    if database_mode == "database_url" and not database_url:
        raise RuntimeError("DATABASE_URL is required in database_url mode")
    if environment in PRODUCTION_ENVIRONMENTS and not database_url:
        raise RuntimeError(
            f"DATABASE_URL is required when TRIDENT_ENV={environment}; "
            "set TRIDENT_DATABASE_MODE=sqlite explicitly for a single-instance demo"
        )
    return bool(database_url)


def uvicorn_command(database_mode: str | None = None) -> list[str]:
    port = os.getenv("PORT", "8000").strip()
    workers = os.getenv("WEB_CONCURRENCY", "1").strip()
    if not port.isdigit() or int(port) < 1 or int(port) > 65535:
        raise RuntimeError("PORT must be an integer from 1 to 65535")
    if not workers.isdigit() or int(workers) < 1:
        raise RuntimeError("WEB_CONCURRENCY must be a positive integer")
    resolved_mode = (database_mode or os.getenv("TRIDENT_DATABASE_MODE", "")).strip().lower()
    if resolved_mode == "sqlite" and workers != "1":
        raise RuntimeError("WEB_CONCURRENCY must be 1 when using SQLite")
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "api:app",
        "--host",
        "0.0.0.0",
        "--port",
        port,
        "--workers",
        workers,
        "--proxy-headers",
    ]


def main() -> None:
    environment = deployment_environment()
    database_url = os.getenv("DATABASE_URL", "").strip()
    database_mode = os.getenv("TRIDENT_DATABASE_MODE", "").strip().lower()
    if should_run_migrations(environment, database_url, database_mode):
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            check=True,
        )
    os.execv(sys.executable, uvicorn_command(database_mode))


if __name__ == "__main__":
    main()
