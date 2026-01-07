"""Management command to back up the project's database.

Supports sqlite3 (creates consistent copy and gzips it) and PostgreSQL
(uses `pg_dump` with `-Fc` if available). Backups are written into
`backups/database/` by default with ISO8601 timestamps and rotated to keep
recent N backups where N can be configured with the `BACKUP_KEEP` env var.
"""
from __future__ import annotations

import gzip
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


DEFAULT_BACKUP_DIR = Path(settings.BASE_DIR) / "backups" / "database"
DEFAULT_KEEP = int(os.getenv("BACKUP_KEEP", "7"))


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


class Command(BaseCommand):
    help = "Create a backup of the configured database (sqlite3 or postgresql)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            help="Directory where backups are stored (default: backups/database)",
            default=str(DEFAULT_BACKUP_DIR),
        )
        parser.add_argument(
            "--keep",
            "-k",
            type=int,
            default=DEFAULT_KEEP,
            help="How many recent backups to keep (older ones will be deleted).",
        )
        parser.add_argument(
            "--no-compress",
            action="store_true",
            default=False,
            help="Do not gzip the resulting backup file (sqlite only).",
        )

    def handle(self, *args, **options):
        out_dir = Path(options["output"]).expanduser()
        keep = int(options["keep"])
        compress = not options["no_compress"]

        _ensure_dir(out_dir)

        db = settings.DATABASES["default"]
        engine = db.get("ENGINE", "").lower()

        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        if "sqlite" in engine:
            src = Path(db.get("NAME"))
            if not src.exists():
                raise CommandError(f"SQLite database file not found at {src}")

            tmp_path = out_dir / f"sqlite-{ts}.sqlite"
            final_path = out_dir / f"sqlite-{ts}.sqlite.gz" if compress else out_dir / f"sqlite-{ts}.sqlite"

            # Use sqlite backup API for a consistent copy
            src_conn = sqlite3.connect(str(src))
            dest_conn = sqlite3.connect(str(tmp_path))
            try:
                with dest_conn:
                    src_conn.backup(dest_conn)
            finally:
                dest_conn.close()
                src_conn.close()

            if compress:
                with open(tmp_path, "rb") as f_in, gzip.open(final_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                tmp_path.unlink()

            self.stdout.write(self.style.SUCCESS(f"SQLite backup saved to {final_path}"))

        elif "postgresql" in engine or "postgres" in engine:
            # Prefer raw DATABASE_URL when provided (supports query params like sslmode=require which Neon needs)
            conn_url = os.getenv("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)

            name = db.get("NAME")
            user = db.get("USER") or os.getenv("PGUSER")
            password = db.get("PASSWORD") or os.getenv("PGPASSWORD")
            host = db.get("HOST") or os.getenv("PGHOST") or "localhost"
            port = str(db.get("PORT") or os.getenv("PGPORT") or "5432")

            pg_dump = shutil.which("pg_dump")
            if pg_dump is None:
                raise CommandError("pg_dump not found in PATH. Please install PostgreSQL client tools.")

            final_path = out_dir / f"postgres-{ts}.dump"

            env = os.environ.copy()

            # If a full DATABASE_URL is provided, pass it to pg_dump using -d. This preserves
            # SSL options like ?sslmode=require that Neon requires. Also set PGPASSWORD or
            # PGSSLMODE from the URL when present.
            if conn_url:
                from urllib.parse import urlparse, parse_qs

                parsed = urlparse(conn_url)
                qs = parse_qs(parsed.query)
                if "sslmode" in qs:
                    env.setdefault("PGSSLMODE", qs["sslmode"][0])
                if parsed.password:
                    env.setdefault("PGPASSWORD", parsed.password)

                cmd = [pg_dump, "-Fc", "-d", conn_url, "-f", str(final_path)]

            else:
                if password:
                    env["PGPASSWORD"] = password

                cmd = [
                    pg_dump,
                    "-h",
                    host,
                    "-p",
                    port,
                    "-U",
                    user or "postgres",
                    "-Fc",
                    "-d",
                    name,
                    "-f",
                    str(final_path),
                ]

            try:
                subprocess.run(cmd, check=True, env=env)
            except subprocess.CalledProcessError as exc:
                if final_path.exists():
                    final_path.unlink()
                raise CommandError(f"pg_dump failed: {exc}") from exc

            self.stdout.write(self.style.SUCCESS(f"Postgres dump saved to {final_path}"))

        else:
            raise CommandError(f"Unsupported database engine: {engine}")

        # Rotation: keep only `keep` most recent backups
        files = sorted(out_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if len(files) > keep:
            for old in files[keep:]:
                try:
                    old.unlink()
                    self.stdout.write(self.style.WARNING(f"Removed old backup {old.name}"))
                except Exception:
                    self.stderr.write(f"Failed to remove old backup {old}")

        self.stdout.write(self.style.SUCCESS("Backup complete."))
