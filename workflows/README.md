# Weekly report workflow

Import `weekly-review.n8n.json` into n8n. Set the variable `ATLAS_BACKEND_URL` to the reachable backend URL. Attach a Header Auth credential with header name `X-API-Key` and the backend key to the HTTP Request node. Credentials are intentionally absent from the export. Enable only after a manual test succeeds.

Schedule: Monday 08:00 Asia/Dubai. The request retries up to three times and calls the server-side report endpoint, which saves the report transactionally in PostgreSQL. A deterministic ISO-week identifier makes retries idempotent. The second request in a week returns the original report; later dataset changes do not silently rewrite that historical report. Reports explicitly disclose unchanged monthly data. Failed executions remain visible in n8n; no email or Slack delivery is configured.

The HTTP reporting node was imported with an isolated Header Auth credential and executed successfully using n8n 2.41.6 in Docker. Evidence: `docs/evidence/n8n-verification.json`. The manual test uses a manual trigger. The Monday schedule was separately imported and published as `atlasWeeklySchedule`; scheduler startup is verified separately from an actual scheduled firing. A hosted private Cloud Run endpoint additionally requires an authenticated route from n8n; a header API key alone is not a Cloud Run identity token.

## Reproduce the isolated local schedule

Start the Docker Compose stack, then run `.venv/bin/python scripts/setup_n8n.py`. It imports the schedule and an encrypted credential into the dedicated `atlas-n8n-data` Docker volume. The temporary plaintext credential file is removed afterward. No credentials are committed.

Start the scheduler (no public port is needed):

```bash
docker run -d --name atlas-n8n --restart unless-stopped \
  --network atlas-commercial-intelligence_default \
  -v atlas-n8n-data:/home/node/.n8n \
  -e GENERIC_TIMEZONE=Asia/Dubai \
  n8nio/n8n@sha256:87e0bab2c93192e8dd885ff7b0697c22a1bd97489568a8c67cc140fd7dbb342d
```

The machine and Docker must be running at the scheduled time. Stop with `docker stop atlas-n8n`. This local schedule writes to the isolated demo database, never sends messages, and does not constitute a hosted automation deployment.

Local runtime status: manual report execution is verified. A published one-minute test did not produce a recorded scheduled execution after restart. The temporary test is disabled and the scheduler is stopped; unattended automation remains a release blocker.
