from typing import Literal
from pydantic import BaseModel
from .db import query, metadata

Country = Literal["All markets", "UAE", "Kuwait", "Qatar", "Oman"]
Period = Literal["Q3 2026", "Q2 2026", "YTD 2026", "FY 2025"]
PERIODS = {
    "Q3 2026": ("2026-07-01", "2026-09-01"),
    "Q2 2026": ("2026-04-01", "2026-06-01"),
    "YTD 2026": ("2026-01-01", "2026-09-01"),
    "FY 2025": ("2025-01-01", "2025-12-01"),
}


class Scope(BaseModel):
    country: Country = "All markets"
    period: Period = "Q3 2026"


def where(scope: Scope):
    start, end = PERIODS[scope.period]
    country = (
        "" if scope.country == "All markets" else f" AND country = '{scope.country}'"
    )
    return f"month >= '{start}' AND month <= '{end}'{country}"


def metric_sql(scope: Scope, intent: str):
    condition = where(scope)
    measures = "SUM(revenue) AS revenue, SUM(target) AS target, SUM(revenue)-SUM(target) AS gap, ROUND(100.0*SUM(revenue)/NULLIF(SUM(target),0),2) AS attainment, SUM(prior_year_revenue) AS prior_year_revenue"
    if intent in ("summary", "growth"):
        return f"SELECT {measures} FROM analytics.v_performance WHERE {condition}"
    group = {
        "products": "product",
        "markets": "country",
        "territories": "territory",
        "trend": "month",
    }[intent]
    order = "month" if intent == "trend" else "gap ASC"
    return f"SELECT {group}, {measures} FROM analytics.v_performance WHERE {condition} GROUP BY {group} ORDER BY {order}"


def overview(scope: Scope):
    summary = query(metric_sql(scope, "summary"))["rows"][0]
    prior = summary["prior_year_revenue"]
    summary["growth"] = (summary["revenue"] / prior - 1) * 100 if prior else None
    groups = {
        kind: query(metric_sql(scope, kind))["rows"]
        for kind in ["products", "markets", "territories", "trend"]
    }
    # Show the full reporting year through the selected period, while KPIs stay scoped.
    end = PERIODS[scope.period][1]
    start = end[:4] + "-01-01"
    country = (
        "" if scope.country == "All markets" else f" AND country='{scope.country}'"
    )
    groups["trend"] = query(
        f"SELECT month, SUM(revenue) AS revenue, SUM(target) AS target, SUM(prior_year_revenue) AS prior_year_revenue FROM analytics.v_performance WHERE month >= '{start}' AND month <= '{end}'{country} GROUP BY month ORDER BY month"
    )["rows"]
    total = summary["revenue"]
    for row in groups["products"]:
        row["share"] = 100 * row["revenue"] / total if total else None
    return {
        "summary": summary,
        **groups,
        "scope": scope.model_dump(),
        "metadata": metadata(),
    }
