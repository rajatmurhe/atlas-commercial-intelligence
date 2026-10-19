"""Create an isolated local PostgreSQL cluster and seed the application.

Never touches the user's default PostgreSQL instance. No Docker required.
"""

import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))


def main():
    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    runtime.chmod(0o700)
    pg_data = runtime / "postgres"
    bins = Path(os.environ.get("POSTGRES_BIN", "/usr/local/opt/postgresql@16/bin"))
    if not (bins / "pg_ctl").exists():
        found = shutil.which("pg_ctl")
        if not found:
            raise SystemExit(
                "Install PostgreSQL 16+ or use docker compose. POSTGRES_BIN can point to its bin directory."
            )
        bins = Path(found).parent
    env_file = ROOT / ".env"
    if not env_file.exists():
        admin, app, reader, api = [secrets.token_urlsafe(32) for _ in range(4)]
        env_file.write_text(
            f"ADMIN_DATABASE_URL=postgresql://ciq_admin:{admin}@127.0.0.1:55433/ciq\nDATABASE_URL=postgresql://ciq_app:{app}@127.0.0.1:55433/ciq\nQUERY_DATABASE_URL=postgresql://ciq_reader:{reader}@127.0.0.1:55433/ciq\nAPI_KEY={api}\nBACKEND_URL=http://127.0.0.1:8031\nAGENT_MODE=guided\n"
        )
        env_file.chmod(0o600)
    from ciq.config import settings
    from urllib.parse import urlparse

    cfg = settings()
    admin_url = urlparse(cfg.admin_database_url)
    if admin_url.hostname != "127.0.0.1" or admin_url.port != 55433:
        raise SystemExit(
            "Local bootstrap only supports its dedicated 127.0.0.1:55433 database."
        )
    if not (pg_data / "PG_VERSION").exists():
        pwfile = runtime / "bootstrap-password"
        try:
            pwfile.write_text(admin_url.password)
            pwfile.chmod(0o600)
            subprocess.run(
                [
                    str(bins / "initdb"),
                    "-D",
                    str(pg_data),
                    "-U",
                    "ciq_admin",
                    "--locale=C",
                    "--encoding=UTF8",
                    "--auth-local=trust",
                    "--auth-host=scram-sha-256",
                    f"--pwfile={pwfile}",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        finally:
            pwfile.unlink(missing_ok=True)
    status = subprocess.run(
        [str(bins / "pg_ctl"), "-D", str(pg_data), "status"], capture_output=True
    )
    if status.returncode:
        subprocess.run(
            [
                str(bins / "pg_ctl"),
                "-D",
                str(pg_data),
                "-l",
                str(runtime / "postgres.log"),
                "-o",
                f"-p 55433 -h 127.0.0.1 -k /tmp",
                "start",
            ],
            check=True,
        )
    import psycopg
    from psycopg import sql

    with psycopg.connect(
        cfg.admin_database_url.rsplit("/", 1)[0] + "/postgres", autocommit=True
    ) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname='ciq'").fetchone():
            conn.execute("CREATE DATABASE ciq")
        for name, url in [
            ("ciq_app", cfg.database_url),
            ("ciq_reader", cfg.query_database_url),
        ]:
            if not conn.execute(
                "SELECT 1 FROM pg_roles WHERE rolname=%s", (name,)
            ).fetchone():
                conn.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                        sql.Identifier(name), sql.Literal(urlparse(url).password)
                    )
                )
    from ciq.data import load

    result = load()
    print(
        f"Loaded {result['rows']:,} synthetic records; {len(result['quality_checks'])} quality checks passed."
    )
    print(
        "Local PostgreSQL is ready on port 55433. Credentials are stored in ignored .env."
    )


if __name__ == "__main__":
    main()
