"""Create a PostgreSQL backup using `pg_dump`."""

import argparse
import datetime as dt
import os
import subprocess
from pathlib import Path

from sqlalchemy.engine.url import make_url

from app.config import Settings


def _default_output_path() -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path("backups") / f"tarobot-{timestamp}.dump"


def _build_pg_dump_command(output_path: Path) -> tuple[list[str], dict[str, str]]:
    settings = Settings.load(require_bot_token=False)
    url = make_url(settings.database_url)
    pg_url = url.set(drivername="postgresql")

    env = os.environ.copy()
    if pg_url.password:
        env["PGPASSWORD"] = pg_url.password

    host = pg_url.host or "localhost"
    port = str(pg_url.port or 5432)
    user = pg_url.username or "postgres"
    database = pg_url.database or "postgres"

    cmd = [
        "pg_dump",
        "-h",
        host,
        "-p",
        port,
        "-U",
        user,
        "-F",
        "c",
        "-f",
        str(output_path),
        database,
    ]
    return cmd, env


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a PostgreSQL backup for the Tarot bot.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=_default_output_path(),
        help="Path to save the dump (default: backups/tarobot-<timestamp>.dump)",
    )
    args = parser.parse_args()

    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd, env = _build_pg_dump_command(output_path)
    subprocess.run(cmd, env=env, check=True)
    print(f"Backup saved to {output_path}")


if __name__ == "__main__":
    main()
