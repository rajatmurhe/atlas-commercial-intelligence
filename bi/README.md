# Business intelligence dashboard handoff

Run `python scripts/export_bi.py` from the configured environment. It exports the complete `analytics.v_performance` view, preserving the source data version in `manifest.json`. The fixed export query uses the restricted role. The interactive query tool's 200-row limit does not apply to this trusted batch job.

## Tableau dashboard specification

Connect Tableau Public/Desktop to `portfolio.csv`; set month to Date and revenue/target/gap to decimal. Build a 1200×800 dashboard named “Commercial performance review” with:

1. Country and month-range filters applied to every sheet.
2. Revenue KPI: `SUM([revenue])`.
3. Attainment KPI: `SUM([revenue])/SUM([target])` formatted as a percentage.
4. Growth KPI: `SUM([revenue])/SUM([prior_year_revenue])-1`; suppress incomplete prior-year coverage rather than treating nulls as zero.
5. Monthly revenue line with target comparison.
6. Country bar chart sorted by `SUM([gap])` ascending.
7. Product variance bar chart, with a zero reference line.
8. Footer: “Synthetic data · Reporting USD · [data version from manifest]”.

Use the same country and date filters as the web dashboard to reconcile totals. Do not average the row-level attainment column. Portfolio share requires the selected portfolio denominator, not a market total.

This folder contains an export script and dashboard specification, not a completed Tableau workbook. A native workbook and screenshot require Tableau authoring and visual QA; they are not claimed here.

The verified export has 12,288 rows; Q3 2026 revenue and target totals reconcile with the API.
