# Deployment handoff

## Local Docker
Run `python3 scripts/compose_env.py`, then `docker compose --env-file .env.compose up --build`. Open `http://localhost:3032`. Database and Redis ports are private to the Compose network. Credentials are separate from the native local stack. The initializer recreates the synthetic warehouse; use this stack only for the demo dataset. Docker daemon must be running.

## Managed PostgreSQL
Create an empty dedicated database and provision `ciq_app` and `ciq_reader` using `scripts/init_database.py` with three explicitly configured TLS connection strings. The admin role needs permission to create roles and schemas. The API must never receive the admin connection string. Provider support for role creation must be checked before choosing a free plan. Do not run the seed loader against an unrelated database.

## Cloud Run
The root Dockerfile is ready for source builds. Configure project/region/runtime service account and create Secret Manager resources named `atlas-app-database`, `atlas-reader-database`, and `atlas-api-key`. Grant only the runtime identity access to those secrets. Run `infra/deploy-cloud-run.sh` from the repository root after credentials, billing, build permissions and destination have been confirmed. The script deploys a private service by default.

## Vercel
Import `apps/web` as a Next.js project. Set server-only `BACKEND_URL`, `API_KEY`, and `APP_ORIGIN` (the exact deployed frontend origin). Do not use NEXT_PUBLIC variables for secrets. The current proxy sends an API key but does not mint GCP identity tokens. Before a Vercel→Cloud Run release, implement workload identity authentication for the private service, or explicitly choose public network invocation while retaining API-key enforcement and global abuse controls. The provided script does not silently make Cloud Run public.

## Release gates
- Docker image build and Compose integration tests (daemon unavailable in initial environment).
- Live model evaluation with a user-selected model and spending budget.
- Remote Langfuse trace verification, including failures.
- Global quota and abuse controls for the public frontend.
- Browser accessibility and visual review.

No hosted URL is claimed until the deployment is actually verified.
