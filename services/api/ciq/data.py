"""Seeded commercial simulation. All names, values and effects are fictional."""

import hashlib
import json
import math
import random
import uuid
from collections import Counter
from datetime import date
from decimal import Decimal

import psycopg
from psycopg.types.json import Jsonb
from .config import ROOT, settings

SEED = 422804
PRODUCTS = [
    (1, "Oncora", "Oncology", 490),
    (2, "Velora", "Oncology", 365),
    (3, "Immunex", "Vaccines", 155),
    (4, "Vaxora", "Vaccines", 120),
    (5, "Cardeva", "Cardiometabolic", 84),
    (6, "Glycera", "Cardiometabolic", 67),
    (7, "Respira", "Respiratory", 92),
    (8, "Aerion", "Respiratory", 75),
]
COUNTRIES = ["UAE", "Kuwait", "Qatar", "Oman"]


def generate(seed: int = SEED):
    rng = random.Random(seed)
    months = [date(2022 + (9 + i) // 12, (9 + i) % 12 + 1, 1) for i in range(48)]
    regions = [
        (i + 1, f"{country} {direction}", country)
        for i, (country, direction) in enumerate(
            (c, d) for c in COUNTRIES for d in ["Central", "North", "East", "West"]
        )
    ]
    sales, targets = [], []
    treated = set(rng.sample(range(1, 17), 8))
    for index, month in enumerate(months):
        for pid, product, category, price in PRODUCTS:
            for rid, _, country in regions:
                for cid in [1, 2]:
                    scale = {"UAE": 1.7, "Kuwait": 0.95, "Qatar": 0.85, "Oman": 0.75}[
                        country
                    ]
                    seasonal = 1 + 0.12 * math.sin((month.month - 2) * math.pi / 6)
                    base = (
                        (95 + pid * 6)
                        * scale
                        * (1 + index * 0.006)
                        * seasonal
                        * (1 if cid == 1 else 0.62)
                    )
                    promo = (
                        pid == 3
                        and rid in treated
                        and date(2025, 4, 1) <= month <= date(2025, 6, 1)
                    )
                    # Campaign and drop labels are never exposed in analytical views.
                    drop = (
                        0.64
                        if country == "Kuwait"
                        and pid in [1, 2]
                        and month >= date(2026, 7, 1)
                        else 1
                    )
                    budget = round(base * price * 1.055, 2)
                    targets.append((month, pid, rid, cid, Decimal(str(budget))))
                    for offset in [0, 1]:
                        rep = (rid - 1) * 2 + offset + 1
                        units = max(
                            0,
                            round(
                                base
                                * 0.5
                                * rng.uniform(0.91, 1.09)
                                * drop
                                * (1.14 if promo else 1)
                            ),
                        )
                        revenue = Decimal(
                            str(round(units * price * (1 + 0.015 * index / 12), 2))
                        )
                        sales.append((month, pid, rid, rep, cid, units, revenue, promo))
    digest = hashlib.sha256(
        json.dumps(sales, default=str, separators=(",", ":")).encode()
    ).hexdigest()[:12]
    return dict(
        months=months,
        regions=regions,
        sales=sales,
        targets=targets,
        data_version=f"seed-{seed}-v1-{digest}",
        treated=sorted(treated),
    )


def quality(data):
    rows = data["sales"]
    keys = [r[:5] for r in rows]
    expected = len(data["months"]) * len(PRODUCTS) * len(data["regions"]) * 2 * 2
    return {
        "no_nulls": all(all(v is not None for v in row) for row in rows),
        "unique_sales_grain": len(keys) == len(set(keys)),
        "nonnegative_measures": all(r[5] >= 0 and r[6] >= 0 for r in rows),
        "rep_territory_integrity": all((r[3] - 1) // 2 + 1 == r[2] for r in rows),
        "complete_monthly_panel": len(rows) == expected
        and all(n == expected // 48 for n in Counter(r[0] for r in rows).values()),
        "unique_target_grain": len(data["targets"])
        == len(set(r[:4] for r in data["targets"])),
        "target_coverage": set(r[:3] + (r[4],) for r in rows)
        == set(r[:4] for r in data["targets"]),
        "target_ranges": all(r[4] >= 0 for r in data["targets"]),
    }


def load(seed: int = SEED):
    cfg, run_id = settings(), str(uuid.uuid4())
    data = generate(seed)
    with psycopg.connect(cfg.admin_database_url, autocommit=True) as conn:
        conn.execute((ROOT / "database/001_initial.sql").read_text())
        conn.execute(
            "INSERT INTO app.etl_runs (run_id,status,seed) VALUES (%s,%s,%s)",
            (run_id, "running", seed),
        )
        checks = quality(data)
        for name, passed in checks.items():
            conn.execute(
                "INSERT INTO app.dq_results VALUES (%s,%s,%s,%s)",
                (run_id, name, passed, Jsonb({"rows": len(data["sales"])})),
            )
        try:
            if not all(checks.values()):
                raise ValueError(
                    "Data quality checks failed; existing dataset retained."
                )
            with conn.transaction():
                conn.execute(
                    "TRUNCATE warehouse.fact_sales, warehouse.fact_targets, warehouse.dim_rep, warehouse.dim_product, warehouse.dim_region, warehouse.dim_date, warehouse.dim_channel"
                )
                with conn.cursor() as cur:
                    cur.executemany(
                        "INSERT INTO warehouse.dim_date VALUES (%s,%s,%s,%s)",
                        [
                            (m, m.year, (m.month - 1) // 3 + 1, m.month)
                            for m in data["months"]
                        ],
                    )
                    cur.executemany(
                        "INSERT INTO warehouse.dim_product VALUES (%s,%s,%s,%s)",
                        [(p, n, c, date(2022, 10, 1)) for p, n, c, _ in PRODUCTS],
                    )
                    cur.executemany(
                        "INSERT INTO warehouse.dim_region VALUES (%s,%s,%s)",
                        data["regions"],
                    )
                    cur.executemany(
                        "INSERT INTO warehouse.dim_rep VALUES (%s,%s,%s)",
                        [(i, f"Rep {i:02}", (i - 1) // 2 + 1) for i in range(1, 33)],
                    )
                    cur.executemany(
                        "INSERT INTO warehouse.dim_channel VALUES (%s,%s)",
                        [(1, "Institutional"), (2, "Retail")],
                    )
                    for table, rows in [
                        ("fact_sales", data["sales"]),
                        ("fact_targets", data["targets"]),
                    ]:
                        with cur.copy(f"COPY warehouse.{table} FROM STDIN") as copy:
                            for row in rows:
                                copy.write_row(row)
                metadata = {
                    "data_version": data["data_version"],
                    "seed": seed,
                    "rows": len(data["sales"]),
                    "months": 48,
                    "start": "2022-10-01",
                    "as_of": "2026-09-30",
                    "currency": "USD",
                    "synthetic": True,
                    "quality_checks": checks,
                }
                conn.execute(
                    "INSERT INTO app.metadata VALUES ('dataset',%s) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (Jsonb(metadata),),
                )
                conn.execute(
                    "UPDATE app.etl_runs SET status='success', finished_at=now(), accepted=%s, data_version=%s WHERE run_id=%s",
                    (len(data["sales"]), data["data_version"], run_id),
                )
        except Exception as exc:
            conn.execute(
                "UPDATE app.etl_runs SET status='failed',finished_at=now(),error=%s WHERE run_id=%s",
                (str(exc), run_id),
            )
            raise
    return metadata


if __name__ == "__main__":
    print(json.dumps(load(), indent=2))
