"""Smoke-test one real model answer and read back its remote trace (no secrets logged)."""

import json
import sys
import uuid
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
import httpx
from ciq.agent import run_agent
from ciq.config import settings
from langfuse import get_client


def main():
    cfg = settings()
    if cfg.agent_mode != "live":
        raise SystemExit("Set AGENT_MODE=live first.")
    answer = run_agent("Show revenue in Kuwait", str(uuid.uuid4()))
    assert answer["status"] == "answered" and answer["scope"]["country"] == "Kuwait"
    now = datetime.now(timezone.utc)
    verified = False
    if cfg.langfuse_public_key and cfg.langfuse_secret_key:
        get_client(public_key=cfg.langfuse_public_key).flush()
        for attempt in range(6):
            response = httpx.get(
                cfg.langfuse_base_url.rstrip("/") + "/api/public/v2/observations",
                auth=(cfg.langfuse_public_key, cfg.langfuse_secret_key),
                params={
                    "fromStartTime": (now - timedelta(hours=1)).isoformat(),
                    "toStartTime": (now + timedelta(minutes=1)).isoformat(),
                    "limit": 100,
                    "fields": "core,basic,metadata",
                },
                timeout=30,
            )
            if response.status_code == 200:
                verified = any(
                    answer["run_id"] in json.dumps(o.get("metadata", {}))
                    for o in response.json().get("data", [])
                )
            if verified:
                break
            if attempt < 5:
                time.sleep(5)
    result = {
        "model": cfg.gemini_model if cfg.llm_provider == "gemini" else cfg.openai_model,
        "provider": cfg.llm_provider,
        "run_id": answer["run_id"],
        "status": answer["status"],
        "scope": answer["scope"],
        "usage": answer["usage"],
        "remote_trace_verified": verified,
        "verified_at": now.isoformat(),
    }
    (ROOT / "docs/evidence/gemini-langfuse-smoke.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
