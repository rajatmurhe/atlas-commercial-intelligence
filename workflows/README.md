# Weekly report workflow

Import `weekly-review.n8n.json` into n8n. Set the variable `ATLAS_BACKEND_URL` to the reachable backend URL. Attach a Header Auth credential with header name `X-API-Key` and the backend key to the HTTP Request node. Credentials are intentionally absent from the export. Enable only after a manual test succeeds.

Schedule: Monday 08:00 Asia/Dubai. The request retries up to three times and calls the server-side report endpoint, which saves the report transactionally in PostgreSQL. A deterministic ISO-week identifier makes retries idempotent. The second request in a week returns the original report; later dataset changes do not silently rewrite that historical report. Reports explicitly disclose unchanged monthly data. Failed executions remain visible in n8n; no email or Slack delivery is configured.

The workflow JSON is prepared, not activated or tested in an n8n installation. A hosted private Cloud Run endpoint additionally requires an authenticated route from n8n; a header API key alone is not a Cloud Run identity token.
