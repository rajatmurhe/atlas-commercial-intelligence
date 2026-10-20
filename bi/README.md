# Tableau handoff

The workbook is generated from the same synthetic portfolio export used by the web dashboard. Run `python scripts/export_bi.py` to refresh `portfolio.csv` and its `manifest.json`, then run `python scripts/build_tableau.py` to build the workbook package.

`atlas-commercial-review.twbx` contains the CSV, manifest, six views (monthly revenue, revenue by market, product plan variance, attainment by market, revenue by channel, and portfolio revenue), and a dashboard named **Commercial performance review**. The builder starts from a Tableau Desktop 2026.2 workbook saved with the connected text source, then adds native workbook view definitions. The dataset contains 12,288 synthetic rows; it is not MSD or patient data.

## Validation status

The builder checks the CSV row count against the export manifest and verifies that the generated TWB XML includes all six worksheets and the dashboard. The TWBX ZIP structure and embedded CSV are also checked in CI. Numerical reconciliation is separate: `.venv/bin/python scripts/verify_bi.py` compares exported totals with PostgreSQL and requires the local database to be running.

**Native render is still unverified.** Tableau Desktop Free 2026.2 successfully ingested the source CSV (13 fields, 12,288 rows). The earlier hand-authored workbook failed to open because it lacked Tableau-generated workbook metadata; the builder now uses a native Tableau workbook template. During the latest render check, Tableau became unresponsive before it displayed the generated dashboard, and the UI bridge timed out. The current dashboard also does not yet include interactive country and month-range controls or a verified Tableau screenshot. Treat this package as a review candidate until the dashboard opens and its marks and layout are checked in Tableau.

Do not publish the synthetic workbook to Tableau Public. Use the packaged workbook locally in Tableau Desktop Free, or provide the CSV to another BI tool.
