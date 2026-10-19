# Release verification status

- 19 backend tests pass; 60 guided regression cases passed in the published benchmark. Guided scores are not live-model accuracy.
- The latest local Next.js production build passes, including TypeScript checks.
- Docker Compose rebuilt and started successfully on 19 October 2026. Browser-facing HTTP smoke checks passed for overview, quality, analytics, chat, feedback, brief persistence, cross-origin rejection and session isolation. See `docker-smoke.json`.
- The final forecast chart fix is undergoing its own refreshed Docker build; deployment status should be checked against the final commit.
- Desktop overview, investigation, forecast statistics and saved brief creation were inspected. Real screenshots appear in the README; full responsive/accessibility verification remains open.
- n8n manually executed the report node successfully and the weekly schedule is published. Unattended scheduling remains unverified.
- Tableau TWBX is generated and structurally checked; native rendering remains unverified.
- Live model, remote tracing, GCP, Vercel and hosted PostgreSQL are not configured. No hosted release or live-model scores are claimed.
- The demo script is provided; a recorded interactive video remains pending.
