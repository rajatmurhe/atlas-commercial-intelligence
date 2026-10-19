"""Fail-closed SQL policy, shared by API, agent and MCP."""

from sqlglot import exp, parse
from sqlglot.optimizer.scope import traverse_scope

TABLES = {"v_sales_monthly", "v_performance"}
FUNCTIONS = {
    "SUM",
    "COUNT",
    "AVG",
    "MIN",
    "MAX",
    "ROUND",
    "NULLIF",
    "COALESCE",
    "ABS",
    "LAG",
    "LEAD",
    "ROW_NUMBER",
    "RANK",
    "DENSE_RANK",
    "AND",
    "OR",
    "CASE",
    "IF",
    "CAST",
    "SUBSTRING",
    "LOWER",
    "UPPER",
}
MAX_ROWS = 200


class UnsafeQuery(ValueError):
    pass


def validate_sql(sql: str) -> str:
    if len(sql) > 12000:
        raise UnsafeQuery("Query exceeds the size limit.")
    try:
        statements = parse(sql, read="postgres")
    except Exception as exc:
        raise UnsafeQuery("SQL could not be parsed.") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise UnsafeQuery("Only one SELECT statement is allowed.")
    tree = statements[0]
    forbidden = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Create,
        exp.Drop,
        exp.Command,
        exp.Into,
        exp.Lock,
        exp.Union,
        exp.Intersect,
        exp.Except,
    )
    if any(isinstance(node, forbidden) for node in tree.walk()):
        raise UnsafeQuery("Writes, locks and set operations are not allowed.")
    if any(w.args.get("recursive") for w in tree.find_all(exp.With)):
        raise UnsafeQuery("Recursive queries are not allowed.")
    if tree.find(exp.Offset):
        raise UnsafeQuery("Pagination is not available through the query tool.")
    for func in tree.find_all(exp.Func):
        name = func.name.upper() if isinstance(func, exp.Anonymous) else func.sql_name()
        if name not in FUNCTIONS:
            raise UnsafeQuery(f"Function {name} is not approved.")
    tables = list(tree.find_all(exp.Table))
    if not tables:
        raise UnsafeQuery("Query an approved analytical view.")
    for scope in traverse_scope(tree):
        for _, source in scope.sources.items():
            if isinstance(source, exp.Table):
                if (
                    source.name not in TABLES
                    or source.db not in ("", "analytics")
                    or source.catalog
                ):
                    raise UnsafeQuery("Only approved analytical views are available.")
                source.set("db", exp.to_identifier("analytics"))
    for join in tree.find_all(exp.Join):
        if not join.args.get("on") and not join.args.get("using"):
            raise UnsafeQuery("Unbounded cross joins are not allowed.")
    limit = tree.args.get("limit")
    if limit:
        value = limit.expression
        if (
            not isinstance(value, exp.Literal)
            or not value.is_int
            or int(value.this) < 1
        ):
            raise UnsafeQuery("LIMIT must be a positive integer.")
        cap = min(int(value.this), MAX_ROWS)
    else:
        cap = MAX_ROWS
    return tree.limit(cap).sql(dialect="postgres")
