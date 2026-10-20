# Release verification status

- The repository's CI runs the backend/security suite, 60-case guided benchmark, packaged BI reconciliation, and production frontend build.
- Docker Compose rebuilt and started locally on 19 October 2026. Browser-facing HTTP smoke checks passed for overview, investigations, feedback, saved briefs, analytics, authentication, origin rejection, and session isolation. See `docker-smoke.json`.
- The latest local Next.js production build passed, including TypeScript checks. Product screenshots appear in the repository README.
- A live Gemini Flash-Lite smoke run returned a validated analytical plan and database-backed answer. The matching Langfuse graph trace was read back from the configured region; see `gemini-langfuse-smoke.json`. A full live-model prompt comparison and Langfuse dashboard screenshot remain open.
- The n8n workflow returned HTTP 200 in a temporary one-minute trigger test. The test is disabled and the Monday schedule is active; its next weekly run has not yet been observed.
- Tableau Desktop Free 2026.2 ingested the synthetic export (13 fields, 12,288 rows). The workbook builder uses a Tableau-saved native template and generates six worksheet definitions plus a dashboard; XML, archive, row-count, and embedded-file checks pass. The latest Tableau UI attempt stalled before displaying the workbook, so native rendering, interactive country/date filters, and a Tableau screenshot remain unverified.
- GCP Cloud Run, Vercel, and hosted PostgreSQL deployment have not been completed. No hosted release is claimed.
- The included 120-second narrated screenshot walkthrough was decoded successfully. It is a screenshot walkthrough, not a live interaction recording.

Atlas is a local portfolio application using synthetic data, not a production service or a system endorsed by MSD. See the README limitations and deployment guide before describing the project externally.
