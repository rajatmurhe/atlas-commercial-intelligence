#!/usr/bin/env bash
set -euo pipefail
: "${GCP_PROJECT:?Set the intended project ID}"
: "${GCP_REGION:?Set the intended Cloud Run region}"
: "${GCP_SERVICE_ACCOUNT:?Set the runtime service account email}"
# Secret resources must already exist; no secret contents belong in command arguments.
gcloud run deploy atlas-api --source . --project "$GCP_PROJECT" --region "$GCP_REGION" \
  --service-account "$GCP_SERVICE_ACCOUNT" --port 8080 --memory 1Gi --cpu 1 \
  --min-instances 0 --max-instances 2 --concurrency 8 --timeout 60 \
  --set-env-vars AGENT_MODE=guided \
  --set-secrets DATABASE_URL=atlas-app-database:latest,QUERY_DATABASE_URL=atlas-reader-database:latest,API_KEY=atlas-api-key:latest \
  --no-allow-unauthenticated
