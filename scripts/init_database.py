"""Provision application roles in an explicitly configured database, then load data."""

import os
from urllib.parse import urlparse
import psycopg
from psycopg import sql
from ciq.config import settings
from ciq.data import load


def main():
    cfg = settings()
    with psycopg.connect(cfg.admin_database_url, autocommit=True) as conn:
        for name, url in [
            ("ciq_app", cfg.database_url),
            ("ciq_reader", cfg.query_database_url),
        ]:
            password = urlparse(url).password
            if not password:
                raise ValueError("Application roles require passwords.")
            if not conn.execute(
                "SELECT 1 FROM pg_roles WHERE rolname=%s", (name,)
            ).fetchone():
                conn.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                        sql.Identifier(name), sql.Literal(password)
                    )
                )
    print(load())


if __name__ == "__main__":
    main()
