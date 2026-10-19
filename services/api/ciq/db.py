import json
from datetime import date, datetime
from decimal import Decimal
import psycopg
from psycopg.rows import dict_row
from .config import settings
from .security import validate_sql


def normalize(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def app_connection():
    return psycopg.connect(
        settings().database_url, row_factory=dict_row, connect_timeout=5
    )


def query(sql: str, params=None):
    approved = validate_sql(sql)
    with psycopg.connect(
        settings().query_database_url, row_factory=dict_row, connect_timeout=5
    ) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        conn.execute("SET LOCAL statement_timeout = '3000ms'")
        conn.execute("SET LOCAL lock_timeout = '500ms'")
        conn.execute("SET LOCAL search_path = analytics")
        rows = conn.execute(approved, params).fetchall()
    return {
        "sql": approved,
        "rows": normalize(rows),
        "row_count": len(rows),
        "possibly_truncated": len(rows) == 200,
    }


def metadata():
    with app_connection() as conn:
        row = conn.execute(
            "SELECT value FROM app.metadata WHERE key='dataset'"
        ).fetchone()
    if not row:
        raise RuntimeError("Dataset not loaded. Run the bootstrap command.")
    return row["value"]
