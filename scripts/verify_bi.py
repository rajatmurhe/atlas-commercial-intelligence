"""Reconcile the packaged BI export with shared metrics without claiming native rendering."""

import csv
import json
import sys
import zipfile
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
from ciq.metrics import Scope, PERIODS, metric_sql
from ciq.db import query


def main():
    with zipfile.ZipFile(ROOT / "bi/atlas-commercial-review.twbx") as archive:
        names = archive.namelist()
        workbook = next(n for n in names if n.endswith(".twb"))
        source = next(n for n in names if n.endswith("portfolio.csv"))
        tree = ET.fromstring(archive.read(workbook))
        rows = list(csv.DictReader(archive.read(source).decode().splitlines()))
    assert len(rows) == 12288
    assert len(tree.findall(".//worksheet")) == 6
    checks = []
    for country, period in [
        ("All markets", "Q3 2026"),
        ("Kuwait", "YTD 2026"),
        ("Qatar", "FY 2025"),
    ]:
        start, end = PERIODS[period]
        selected = [
            r
            for r in rows
            if start <= r["month"] <= end
            and (country == "All markets" or r["country"] == country)
        ]
        actual = query(metric_sql(Scope(country=country, period=period), "summary"))[
            "rows"
        ][0]
        totals = {
            key: sum(Decimal(r[key]) for r in selected)
            for key in ["revenue", "target", "gap"]
        }
        for key, value in totals.items():
            assert abs(value - Decimal(str(actual[key]))) < Decimal("0.01"), (
                country,
                period,
                key,
            )
        attainment = totals["revenue"] / totals["target"] * 100
        assert abs(attainment - Decimal(str(actual["attainment"]))) <= Decimal("0.005")
        checks.append(
            {
                "country": country,
                "period": period,
                "rows": len(selected),
                "status": "reconciled",
            }
        )
    report = {
        "package_rows": len(rows),
        "worksheets": 6,
        "checks": checks,
        "native_tableau_rendering": "not verified",
    }
    (ROOT / "docs/evidence/bi-reconciliation.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
