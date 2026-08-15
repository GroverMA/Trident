"""Apply database migrations during a Vercel production build."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL is not connected yet; skipping database migrations.")
        return
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
    )


if __name__ == "__main__":
    main()
