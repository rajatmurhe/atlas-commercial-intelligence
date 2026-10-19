"""Local stdio MCP server. Shares the same query policy as the web API."""

from mcp.server.fastmcp import FastMCP
from .db import query
from .metrics import Scope, metric_sql

mcp = FastMCP("Commercial Intelligence")


@mcp.tool()
def list_tables() -> dict:
    """Return approved analytical views and their business meanings."""
    return {
        "analytics.v_sales_monthly": "Monthly product, country, territory and channel revenue, units, target, promotion.",
        "analytics.v_performance": "The same grain plus signed gap, attainment, and prior_year_revenue. Aggregate before calculating ratios.",
    }


@mcp.tool()
def run_query(sql: str) -> dict:
    """Run one validated read-only SELECT; max 200 rows and 3 seconds."""
    return query(sql)


@mcp.tool()
def get_kpi(country: str = "All markets", period: str = "Q3 2026") -> dict:
    """Get revenue, target and attainment using the shared metric contract."""
    return query(metric_sql(Scope(country=country, period=period), "summary"))


if __name__ == "__main__":
    mcp.run(transport="stdio")
