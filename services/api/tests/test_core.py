import uuid
import pytest
from ciq.security import validate_sql, UnsafeQuery
from ciq.data import generate, quality
from ciq.agent import guided_plan, run_agent
from ciq.metrics import Scope, overview


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM warehouse.fact_sales",
        "SELECT * FROM analytics.v_performance; DROP TABLE x",
        "SELECT pg_sleep(10) FROM analytics.v_performance",
        "SELECT * FROM pg_catalog.pg_authid",
        "SELECT * INTO temp_x FROM analytics.v_performance",
        "WITH x AS (DELETE FROM warehouse.fact_sales RETURNING *) SELECT * FROM x",
        "SELECT * FROM analytics.v_performance FOR UPDATE",
        "SELECT * FROM analytics.v_performance a CROSS JOIN analytics.v_performance b",
        "SELECT * FROM analytics.v_performance LIMIT -1",
    ],
)
def test_rejects_unsafe_sql(sql):
    with pytest.raises(UnsafeQuery):
        validate_sql(sql)


def test_caps_limit():
    assert "LIMIT 200" in validate_sql(
        "SELECT * FROM analytics.v_performance LIMIT 10000"
    )


def test_seed_and_integrity():
    a, b = generate(), generate()
    assert a["data_version"] == b["data_version"]
    assert all(quality(a).values())
    a["sales"].append(a["sales"][0])
    assert not quality(a)["unique_sales_grain"]


def test_clarification():
    assert guided_plan("Which market is best?", {}).intent == "clarify"


def test_target_not_multiplied():
    data = generate()
    reference = sum(float(r[4]) for r in data["targets"] if str(r[0]) >= "2026-07-01")
    assert overview(Scope())["summary"]["target"] == pytest.approx(reference)


def test_followup_context():
    sid = str(uuid.uuid4())
    first = run_agent("Which products contributed to the gap in Kuwait?", sid)
    follow = run_agent("What about Qatar?", sid)
    assert first["intent"] == follow["intent"] == "products"
    assert follow["scope"]["country"] == "Qatar"
    assert follow["rows"] != first["rows"]


def test_session_isolation():
    answer = run_agent("Show revenue", str(uuid.uuid4()))
    assert answer["scope"]["country"] == "All markets"


def test_weekly_report_is_idempotent():
    from ciq.main import weekly_report

    first = weekly_report()
    second = weekly_report()
    assert first["report_id"] == second["report_id"]
    assert second["created"] is False
    assert first["content"] == second["content"]
    assert "Synthetic monthly data" in second["content"]["disclosure"]


def test_api_auth_and_session_ownership():
    from fastapi.testclient import TestClient
    from ciq.main import app
    from ciq.config import settings

    client = TestClient(app)
    assert client.get("/api/overview").status_code == 401
    headers = {"X-API-Key": settings().api_key}
    sid = str(uuid.uuid4())
    answer = client.post(
        "/api/chat",
        headers=headers,
        json={"question": "Show revenue", "session_id": sid},
    ).json()
    response = client.post(
        "/api/feedback",
        headers=headers,
        json={"run_id": answer["run_id"], "session_id": str(uuid.uuid4()), "vote": 1},
    )
    assert response.status_code == 404


def test_failed_run_has_reference_and_persisted_trace(monkeypatch):
    from fastapi.testclient import TestClient
    import ciq.main as main
    from ciq.config import settings
    from ciq.db import app_connection

    def fail(*args, **kwargs):
        raise RuntimeError("simulated provider failure")

    monkeypatch.setattr(main, "run_agent", fail)
    sid = str(uuid.uuid4())
    response = TestClient(main.app).post(
        "/api/chat",
        headers={"X-API-Key": settings().api_key},
        json={"question": "Show revenue", "session_id": sid},
    )
    assert response.status_code == 503
    with app_connection() as conn:
        row = conn.execute(
            "SELECT response FROM app.runs WHERE session_id=%s", (sid,)
        ).fetchone()
    assert row["response"]["status"] == "error"
    assert row["response"]["run_id"] in response.json()["detail"]


def test_global_budget_is_shared_between_sessions(monkeypatch):
    from ciq.config import settings
    from ciq.quota import reserve_question
    from ciq.db import app_connection
    from fastapi import HTTPException

    # Lower the cap to the existing global count, without deleting shared records.
    reserve_question(str(uuid.uuid4()))
    with app_connection() as conn:
        used = conn.execute(
            "SELECT used FROM app.request_budgets WHERE bucket='global' AND window_start=date_trunc('hour',now())"
        ).fetchone()["used"]
    monkeypatch.setattr(settings(), "global_questions_per_hour", used)
    with pytest.raises(HTTPException) as exc:
        reserve_question(str(uuid.uuid4()))
    assert exc.value.status_code == 429


@pytest.mark.parametrize(
    "question",
    [
        "Show revenue for Oncora",
        "What were oncology sales?",
        "Show hospital revenue",
        "Show sales in Saudi Arabia",
        "Compare UAE and Kuwait revenue",
        "Show Q3 2025 revenue",
        "Show FY 2026 revenue",
        "Show sales in 2030",
        "Compare Q2 and Q3 revenue",
        "What were sales last quarter?",
    ],
)
def test_unsupported_scope_does_not_return_broader_totals(question):
    assert guided_plan(question, {}).intent == "clarify"


def test_live_scope_guard_does_not_call_provider(monkeypatch):
    from ciq.agent import classify
    from ciq.config import settings

    monkeypatch.setattr(settings(), "agent_mode", "live")
    result = classify({"question": "Show Oncora revenue", "context": {}})
    assert result["plan"]["intent"] == "clarify"
    assert result["usage"]["input_tokens"] == 0
