# Release verification status

- 30 backend tests pass; 60 guided regression cases passed in the published benchmark. Guided scores are not live-model accuracy.
- The latest local Next.js production build passes, including TypeScript checks.
- Docker Compose rebuilt and started successfully on 19 October 2026. Browser-facing HTTP smoke checks passed for overview, quality, analytics, chat, feedback, brief persistence, cross-origin rejection and session isolation. See `docker-smoke.json`.
- Docker was rebuilt with the scope guards, ETL statistics refresh and KPI wrapping fix. All nine browser-facing smoke checks passed after the rebuild.
- Desktop overview, investigation, forecast statistics and saved brief creation were inspected. Real screenshots appear in the README. Browser access is currently disabled in Work settings; full responsive/accessibility verification remains open.
- n8n automatic execution passed a temporary one-minute cron test in trigger mode; the API returned HTTP 200. The test is disabled and the Monday schedule is active. Its next Monday firing has not yet been observed.
- Tableau TWBX is structurally checked and its embedded data reconciles revenue, targets, gaps and attainment across three scopes. Native Tableau rendering remains unverified.
- Live model, remote tracing, GCP, Vercel and hosted PostgreSQL are not configured. No hosted release or live-model scores are claimed.
- A 120-second narrated screenshot walkthrough is included and decoded successfully. It is explicitly labeled as a screenshot walkthrough, not a live recording.
