"""Encrypted PostgreSQL backup script.

Creates pg_dump backups encrypted with GPG or openssl.
Run manually or via cron/db-backup container.
"""

import os
import subprocess
import datetime
import sys

DB_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://ia_vendedor:devpassword123@db:5432/ia_vendedor")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/backups")
ENCRYPTION_KEY = os.environ.get("BACKUP_ENCRYPTION_KEY", "")


def parse_db_url(url: str) -> dict:
    """Parse postgresql://user:pass@host:port/db into dict."""
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") or "postgres",
    }


def run_backup():
    creds = parse_db_url(DB_URL)
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"sellia_backup_{timestamp}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    env = os.environ.copy()
    env["PGPASSWORD"] = creds["password"]

    cmd = [
        "pg_dump",
        "-h", creds["host"],
        "-p", str(creds["port"]),
        "-U", creds["user"],
        "-d", creds["database"],
        "-F", "plain",
        "-f", filepath,
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Backup failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Encrypt with openssl if key provided
    if ENCRYPTION_KEY:
        if len(ENCRYPTION_KEY) < 32:
            print(
                f"ERROR: BACKUP_ENCRYPTION_KEY is only {len(ENCRYPTION_KEY)} chars. "
                "It must be at least 32 characters for AES-256 security.",
                file=sys.stderr,
            )
            sys.exit(2)
        encrypted = f"{filepath}.enc"
        enc_cmd = [
            "openssl", "enc", "-aes-256-cbc", "-salt",
            "-pbkdf2", "-iter", "100000",
            "-in", filepath,
            "-out", encrypted,
            "-pass", f"pass:{ENCRYPTION_KEY}",
        ]
        subprocess.run(enc_cmd, check=True)
        os.remove(filepath)
        filepath = encrypted
        print(f"Encrypted backup created: {filepath}")
    else:
        print(f"Backup created (unencrypted): {filepath}")
        print("WARNING: Set BACKUP_ENCRYPTION_KEY for production.")

    # Keep only last 7 backups
    backups = sorted([
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith("sellia_backup_")
    ])
    for old in backups[:-7]:
        os.remove(os.path.join(BACKUP_DIR, old))
        print(f"Removed old backup: {old}")


if __name__ == "__main__":
    run_backup()
