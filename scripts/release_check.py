"""Check release prerequisites without printing any credential values."""

import json
import shutil
import sys
from pathlib import Path
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
cfg = dotenv_values(ROOT / ".env")
checks = {
    "live_model_configured": bool(
        cfg.get("OPENAI_API_KEY") and cfg.get("OPENAI_MODEL")
    ),
    "remote_tracing_configured": bool(
        cfg.get("LANGFUSE_PUBLIC_KEY") and cfg.get("LANGFUSE_SECRET_KEY")
    ),
    "gcloud_installed": bool(shutil.which("gcloud")),
    "gcp_project_selected": bool(cfg.get("GCP_PROJECT")),
    "vercel_project_linked": (ROOT / "apps/web/.vercel/project.json").exists(),
    "hosted_database_configured": bool(
        cfg.get("DATABASE_URL")
        and not any(
            x in cfg["DATABASE_URL"] for x in ("127.0.0.1", "localhost", "@postgres:")
        )
    ),
}
print(json.dumps(checks, indent=2))
if not all(checks.values()):
    sys.exit(1)
