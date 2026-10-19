import hashlib
import hmac
import json
import logging
import time
import uuid
from functools import lru_cache
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb
from .config import settings
from .quota import reserve_question
from .db import app_connection, metadata, normalize
from .metrics import Scope, Country, Period, overview
from .agent import run_agent
from .analysis import analyze, promotion_analysis

logger = logging.getLogger(__name__)
app = FastAPI(
    title="Commercial Intelligence Workbench", version="0.1.0", docs_url="/docs"
)


def authorize(x_api_key: str = Header(default="")):
    if not hmac.compare_digest(x_api_key, settings().api_key):
        raise HTTPException(401, "A valid API key is required.")


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


def cached(key, compute):
    cfg = settings()
    client = None
    if cfg.redis_url:
        try:
            import redis

            client = redis.Redis.from_url(
                cfg.redis_url, socket_timeout=0.3, socket_connect_timeout=0.3
            )
            value = client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            client = None
    result = compute()
    if client:
        try:
            client.setex(key, 300, json.dumps(result))
        except Exception:
            logger.warning("Cache write failed; response remains available.")
    return result


@app.get("/api/overview", dependencies=[Depends(authorize)])
def get_overview(country: Country = "All markets", period: Period = "Q3 2026"):
    scope = Scope(country=country, period=period)
    version = metadata()["data_version"]
    return cached(f"overview:{version}:{country}:{period}", lambda: overview(scope))


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1500)
    session_id: UUID
    scope: Scope | None = None


@app.post("/api/chat", dependencies=[Depends(authorize)])
def chat(body: ChatRequest):
    reserve_question(str(body.session_id))
    started = time.perf_counter()
    try:
        return run_agent(
            body.question,
            str(body.session_id),
            body.scope.model_dump() if body.scope else None,
        )
    except Exception as exc:
        failure_id = str(uuid.uuid4())
        elapsed = round((time.perf_counter() - started) * 1000)
        logger.exception("Agent execution failed: %s", failure_id)
        try:
            with app_connection() as conn:
                conn.execute(
                    "INSERT INTO app.runs(run_id,session_id,question,response,latency_ms) VALUES(%s,%s,%s,%s,%s)",
                    (
                        failure_id,
                        body.session_id,
                        body.question,
                        Jsonb(
                            {
                                "status": "error",
                                "error_type": type(exc).__name__,
                                "run_id": failure_id,
                            }
                        ),
                        elapsed,
                    ),
                )
        except Exception:
            logger.exception("Failure record could not be persisted: %s", failure_id)
        raise HTTPException(
            503, f"The investigation could not finish. Reference: {failure_id}"
        )


class Feedback(BaseModel):
    session_id: UUID
    run_id: UUID
    vote: Literal[-1, 1]


@app.post("/api/feedback", dependencies=[Depends(authorize)])
def feedback(body: Feedback):
    with app_connection() as conn:
        if not conn.execute(
            "SELECT 1 FROM app.runs WHERE run_id=%s AND session_id=%s",
            (body.run_id, body.session_id),
        ).fetchone():
            raise HTTPException(404, "Investigation not found in this session.")
        conn.execute(
            "INSERT INTO app.feedback(run_id,session_id,vote) VALUES(%s,%s,%s) ON CONFLICT(run_id,session_id) DO UPDATE SET vote=excluded.vote",
            (body.run_id, body.session_id, body.vote),
        )
    return {"saved": True}


class BriefRequest(BaseModel):
    session_id: UUID
    country: Country = "All markets"
    period: Period = "Q3 2026"


@app.post("/api/briefs", dependencies=[Depends(authorize)])
def create_brief(body: BriefRequest):
    data = overview(Scope(country=body.country, period=body.period))
    s = data["summary"]
    title = f"{body.country} · {body.period} commercial review"
    content = {
        "summary": f"Revenue of ${s['revenue']:,.0f} reached {s['attainment']:.1f}% of target. The signed gap was ${s['gap']:,.0f}.",
        "scope": data["scope"],
        "data_version": data["metadata"]["data_version"],
        "findings": [
            f"{r['product']}: ${r['gap']:,.0f} to target, {r['attainment']:.1f}% attainment."
            for r in data["products"][:3]
        ],
        "next_step": "Review negative gaps with territory owners and check order timing. These observations do not establish causes.",
        "disclosure": "Synthetic data. Reporting USD. A draft for human review.",
    }
    brief_id = str(uuid.uuid4())
    with app_connection() as conn:
        conn.execute(
            "INSERT INTO app.briefs(brief_id,session_id,title,content) VALUES(%s,%s,%s,%s)",
            (brief_id, body.session_id, title, Jsonb(content)),
        )
    return {"brief_id": brief_id, "title": title, "content": content}


@app.get("/api/briefs", dependencies=[Depends(authorize)])
def get_briefs(session_id: UUID):
    with app_connection() as conn:
        rows = conn.execute(
            "SELECT brief_id::text,title,content,created_at FROM app.briefs WHERE session_id=%s ORDER BY created_at DESC LIMIT 30",
            (session_id,),
        ).fetchall()
    return normalize(rows)


@app.get("/api/quality", dependencies=[Depends(authorize)])
def quality():
    with app_connection() as conn:
        runs = conn.execute(
            "SELECT run_id::text,status,started_at,finished_at,accepted,rejected,data_version FROM app.etl_runs ORDER BY started_at DESC LIMIT 5"
        ).fetchall()
    return {
        "metadata": metadata(),
        "runs": normalize(runs),
        "agent_mode": settings().agent_mode,
        "tracing": "langfuse"
        if settings().langfuse_secret_key
        else "local PostgreSQL run log",
        "limitations": [
            "All data is synthetic and contains no MSD records.",
            "Guided mode supports a bounded question vocabulary; it is not a live LLM.",
            "Forecast bands are exploratory and uncalibrated.",
            "Live model comparisons require configured model credentials.",
        ],
    }


@lru_cache(maxsize=10)
def cached_analysis(version, country):
    return {**analyze(country), "promotion": promotion_analysis()}


@app.get("/api/analysis", dependencies=[Depends(authorize)])
def analysis(country: Country = "All markets"):
    return cached_analysis(metadata()["data_version"], country)


@app.post("/api/reports/weekly", dependencies=[Depends(authorize)])
def weekly_report():
    """Idempotent weekly snapshot for the authenticated reporting integration."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("Asia/Dubai"))
    year, week, _ = now.isocalendar()
    scope = Scope()
    dataset = metadata()
    report_key = f"{year}-W{week:02}:{scope.country}:{scope.period}"
    report_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "atlas:weekly:" + report_key))
    session_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "atlas:weekly-reports"))
    with app_connection() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (report_key,))
        existing = conn.execute(
            "SELECT title,content FROM app.briefs WHERE brief_id=%s", (report_id,)
        ).fetchone()
        if existing:
            return {"report_id": report_id, "created": False, **existing}
        prior = conn.execute(
            "SELECT content FROM app.briefs WHERE session_id=%s ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        unchanged = bool(
            prior and prior["content"].get("data_version") == dataset["data_version"]
        )
        data = overview(scope)
        s = data["summary"]
        title = f"Weekly commercial review · {year}-W{week:02}"
        content = {
            "data_version": dataset["data_version"],
            "scope": scope.model_dump(),
            "summary": f"Revenue: ${s['revenue']:,.0f}; attainment: {s['attainment']:.1f}%; signed gap: ${s['gap']:,.0f}.",
            "findings": [
                f"{r['product']}: ${r['gap']:,.0f} signed gap."
                for r in data["products"][:3]
            ],
            "data_status": "No new dataset since the previous report."
            if unchanged
            else "Dataset snapshot captured.",
            "disclosure": "Synthetic monthly data through September 2026. Weekly execution does not imply weekly sales updates.",
            "next_step": "Review product contributions and order timing with territory owners; no causal conclusion is established.",
        }
        conn.execute(
            "INSERT INTO app.briefs(brief_id,session_id,title,content) VALUES(%s,%s,%s,%s)",
            (report_id, session_id, title, Jsonb(content)),
        )
    return {"report_id": report_id, "created": True, "title": title, "content": content}
