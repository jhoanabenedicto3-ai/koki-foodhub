import gzip
import os
import sqlite3
from tempfile import TemporaryDirectory
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings


class BackupCommandTests(TestCase):
    def test_sqlite_backup_creates_gz_file(self):
        with TemporaryDirectory() as td:
            td_path = Path(td)
            db_file = td_path / "test.db"

            # Create a simple sqlite db
            conn = sqlite3.connect(db_file)
            conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, text TEXT)")
            conn.execute("INSERT INTO t (text) VALUES (?)", ("hello",))
            conn.commit()
            conn.close()

            db_settings = settings.DATABASES.copy()
            db_settings["default"] = {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": str(db_file),
            }

            with override_settings(DATABASES=db_settings):
                call_command("backup_db", "--output", str(td_path))

            # Find a gz file written
            gz_files = list(td_path.glob("*.gz"))
            self.assertTrue(len(gz_files) >= 1, f"No gz backup found in {td_path}")

            # Ensure gzip file can be opened
            with gzip.open(gz_files[0], "rb") as fh:
                data = fh.read(100)
                self.assertTrue(len(data) > 0)
