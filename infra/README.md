# Deployment handoff

## Local Docker
Run `python3 scripts/compose_env.py`, then `docker compose --env-file .env.compose up --build`. Open `http://localhost:3032`. Database and Redis ports are private to the Compose network. Credentials are separate from the native local stack. The initializer recreates the synthetic warehouse; use this stack only for the demo dataset. Docker daemon must be running.

## Managed PostgreSQL
Create an empty dedicated database and provision `ciq_app` and `ciq_reader` using `scripts/init_database.py` with three explicitly configured TLS connection strings. The admin role needs permission to create roles and schemas. The API must never receive the admin connection string. Provider support for role creation must be checked before choosing a free plan. Do not run the seed loader against an unrelated database.

## Cloud Run
The root Dockerfile is ready for source builds. Configure project/region/runtime service account and create Secret Manager resources named `atlas-app-database`, `atlas-reader-database`, and `atlas-api-key`. Grant only the runtime identity access to those secrets. Run `infra/deploy-cloud-run.sh` from the repository root after credentials, billing, build permissions and destination have been confirmed. The script deploys a private service by default.

## Vercel
Import `apps/web` as a Next.js project. Set server-only `BACKEND_URL`, `API_KEY`, and `APP_ORIGIN` (the exact deployed frontend origin). Do not use NEXT_PUBLIC variables for secrets. The proxy supports private Cloud Run invocation with `BACKEND_AUTH_MODE=gcp-oidc`. Set `GCP_WORKLOAD_IDENTITY_PROVIDER` to `//iam.googleapis.com/projects/NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER` and `GCP_INVOKER_SERVICE_ACCOUNT` to the dedicated invoker identity. `BACKEND_URL` must be the canonical Cloud Run service origin.

Configure a Vercel OIDC provider in GCP, allowing the exact Vercel team audience and restricting the subject to your project and production environment. Grant that principal `roles/iam.workloadIdentityUser` on the invoker account; grant the invoker `roles/run.invoker` only on Atlas. Enable IAM Credentials and STS APIs. The runtime service account remains separate and owns database-secret access. No JSON service-account key is needed.

The implementation exchanges the Vercel token through STS and obtains an audience-bound ID token through IAM Credentials. API-key enforcement still applies. Source: [Vercel federation guide](https://vercel.com/docs/oidc/gcp), [Google token exchange](https://cloud.google.com/iam/docs/reference/sts/rest/v1/TopLevel/token), [ID-token generation](https://cloud.google.com/iam/docs/reference/credentials/rest/v1/projects.serviceAccounts/generateIdToken). This path is implemented but awaits verification against the user's projects.


## Release gates
- Docker image build and Compose integration tests (daemon unavailable in initial environment).
- Live model evaluation with a user-selected model and spending budget.
- Remote Langfuse trace verification, including failures.
- Exercise the database-backed global and per-session hourly budgets in the hosted environment. Defaults: 200 globally, 30 per session. Failed calls count; the global budget cannot be bypassed by clearing cookies.
- Browser accessibility and visual review.

No hosted URL is claimed until the deployment is actually verified.
