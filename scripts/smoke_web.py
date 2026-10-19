"""Exercise the browser-facing API of a running native or Docker release."""

import argparse
import json
from pathlib import Path
import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", default="http://localhost:3032")
    parser.add_argument("--output", default="docs/evidence/docker-smoke.json")
    args = parser.parse_args()
    checks = {}
    with httpx.Client(
        base_url=args.origin, headers={"Origin": args.origin}, timeout=60
    ) as client:
        for route in ("/", "/api/overview", "/api/quality", "/api/analysis"):
            response = client.get(route)
            response.raise_for_status()
            checks[route] = response.status_code
        if args.origin in ("http://localhost:3032", "http://127.0.0.1:3031"):
            cookie = response.cookies.get("ciq_session")
            assert cookie
            client.headers["Cookie"] = "ciq_session=" + cookie
        answer = client.post("/api/chat", json={"question": "Show revenue in Kuwait"})
        answer.raise_for_status()
        assert answer.json()["scope"]["country"] == "Kuwait"
        assert answer.json()["status"] == "answered"
        checks["chat"] = "answered"
        response = client.post(
            "/api/feedback", json={"run_id": answer.json()["run_id"], "vote": 1}
        )
        response.raise_for_status()
        checks["feedback"] = "saved"
        brief = client.post("/api/briefs", json={})
        brief.raise_for_status()
        listing = client.get("/api/briefs")
        listing.raise_for_status()
        assert any(
            item["brief_id"] == brief.json()["brief_id"] for item in listing.json()
        )
        checks["brief"] = "saved and retrieved"
        denied = client.post(
            "/api/chat",
            headers={"Origin": "https://invalid.example"},
            json={"question": "Show revenue"},
        )
        assert denied.status_code == 403
        checks["cross_origin_post"] = "rejected"
    with httpx.Client(
        base_url=args.origin, headers={"Origin": args.origin}, timeout=60
    ) as other:
        denied = other.post(
            "/api/feedback", json={"run_id": answer.json()["run_id"], "vote": 1}
        )
        assert denied.status_code == 404
        checks["session_isolation"] = "enforced"
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(checks, indent=2))
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
