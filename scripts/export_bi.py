"""Export the same approved analytical view for BI, without the interactive row cap.

This is a trusted export job with a fixed query, not a user-supplied query tool.
"""

import csv
import json
import sys
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
from ciq.config import settings
from ciq.db import metadata


def main():
    output = ROOT / "bi"
    output.mkdir(exist_ok=True)
    with psycopg.connect(settings().query_database_url, row_factory=dict_row) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        rows = conn.execute(
            "SELECT * FROM analytics.v_performance ORDER BY month,country,territory,product,channel"
        ).fetchall()
    with (output / "portfolio.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "manifest.json").write_text(
        json.dumps(
            {
                **metadata(),
                "export_rows": len(rows),
                "source": "analytics.v_performance",
            },
            indent=2,
        )
    )
    print(f"Exported {len(rows):,} rows to bi/portfolio.csv")


if __name__ == "__main__":
    main()
