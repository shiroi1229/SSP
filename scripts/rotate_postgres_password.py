#!/usr/bin/env python3
"""Rotate the SSP PostgreSQL password without printing the new secret.

Run this on the machine that can reach PostgreSQL and that owns the local .env:

    python scripts/rotate_postgres_password.py

The script:
1. Loads the current local .env.
2. Generates a strong random replacement password.
3. Stages an updated .env in the same directory.
4. Changes the PostgreSQL role password.
5. Atomically replaces .env only after the database change succeeds.
6. Verifies a fresh connection using the new password.

The new password is never printed or written to Git-tracked files.
"""

from __future__ import annotations

import os
import secrets
import stat
import sys
import tempfile
from pathlib import Path

import psycopg2
from dotenv import dotenv_values
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def _require(value: str | None, name: str) -> str:
    if value is None or not str(value).strip():
        raise RuntimeError(f"{name} is required in {ENV_PATH}")
    return str(value).strip()


def _load_config() -> dict[str, str]:
    if not ENV_PATH.exists():
        raise FileNotFoundError(
            f"Local {ENV_PATH.name} was not found. Copy .env.example to .env and configure it first."
        )

    values = dotenv_values(ENV_PATH)
    return {
        "host": _require(values.get("POSTGRES_HOST"), "POSTGRES_HOST"),
        "port": _require(values.get("POSTGRES_PORT"), "POSTGRES_PORT"),
        "dbname": _require(values.get("POSTGRES_DB"), "POSTGRES_DB"),
        "user": _require(values.get("POSTGRES_USER"), "POSTGRES_USER"),
        "password": _require(values.get("POSTGRES_PASSWORD"), "POSTGRES_PASSWORD"),
    }


def _render_updated_env(new_password: str) -> str:
    original = ENV_PATH.read_text(encoding="utf-8-sig")
    lines = original.splitlines(keepends=True)
    output: list[str] = []
    replaced = False

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("POSTGRES_PASSWORD="):
            newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            prefix = line[: len(line) - len(stripped)]
            output.append(f"{prefix}POSTGRES_PASSWORD={new_password}{newline}")
            replaced = True
        else:
            output.append(line)

    if not replaced:
        if output and not output[-1].endswith(("\n", "\r\n")):
            output.append("\n")
        output.append(f"POSTGRES_PASSWORD={new_password}\n")

    return "".join(output)


def _stage_env(content: str) -> Path:
    original_mode = stat.S_IMODE(ENV_PATH.stat().st_mode)
    fd, temp_name = tempfile.mkstemp(prefix=".env.rotate-", dir=ENV_PATH.parent, text=True)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, original_mode)
        return temp_path
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        finally:
            raise


def _connect(config: dict[str, str], password: str):
    return psycopg2.connect(
        host=config["host"],
        port=int(config["port"]),
        dbname=config["dbname"],
        user=config["user"],
        password=password,
        connect_timeout=10,
    )


def main() -> int:
    staged_path: Path | None = None
    db_rotated = False
    try:
        config = _load_config()
        new_password = secrets.token_urlsafe(48)
        staged_path = _stage_env(_render_updated_env(new_password))

        with _connect(config, config["password"]) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("ALTER ROLE {} WITH PASSWORD {}").format(
                        sql.Identifier(config["user"]),
                        sql.Literal(new_password),
                    )
                )
            conn.commit()
        db_rotated = True

        # The DB now uses the new credential. Make the local config switch atomic.
        os.replace(staged_path, ENV_PATH)
        staged_path = None

        # Verify from a brand-new connection using the replacement credential.
        with _connect(config, new_password) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                if cur.fetchone() != (1,):
                    raise RuntimeError("Post-rotation verification returned an unexpected result")

        print("PostgreSQL credential rotation completed and verified.")
        print("The new password was stored only in the local .env and was not printed.")
        return 0

    except Exception as exc:
        print(f"Rotation failed: {exc}", file=sys.stderr)
        if staged_path and staged_path.exists():
            if db_rotated:
                # The database already accepted the replacement password. Preserve the
                # staged .env so the operator can recover without exposing the secret.
                print(
                    "Database password changed, but .env replacement failed. "
                    f"Recovery file preserved at: {staged_path}",
                    file=sys.stderr,
                )
                print(
                    "Move that file to .env on this host before restarting SSP.",
                    file=sys.stderr,
                )
            else:
                try:
                    staged_path.unlink()
                except OSError:
                    print(
                        f"Warning: remove temporary credential file manually: {staged_path}",
                        file=sys.stderr,
                    )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
