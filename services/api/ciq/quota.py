"""Atomic database-backed request budgets shared by all API workers."""

from fastapi import HTTPException
from .config import settings
from .db import app_connection


def reserve_question(session_id: str):
    cfg = settings()
    # The transaction reserves both counters or neither. Failed model calls count.
    with app_connection() as conn:
        for name, window, limit in (
            ("global", "hour", cfg.global_questions_per_hour),
            ("session:" + session_id, "hour", cfg.session_questions_per_hour),
        ):
            row = conn.execute(
                """INSERT INTO app.request_budgets(bucket, window_start, used)
                VALUES (%s, date_trunc(%s, now()), 1)
                ON CONFLICT(bucket, window_start) DO UPDATE
                SET used = app.request_budgets.used + 1
                WHERE app.request_budgets.used < %s
                RETURNING used""",
                (name, window, limit),
            ).fetchone()
            if not row:
                raise HTTPException(
                    429,
                    "The hourly investigation budget is exhausted. Try again next hour.",
                    headers={"Retry-After": "3600"},
                )
