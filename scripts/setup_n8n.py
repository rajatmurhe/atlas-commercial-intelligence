"""Provision Atlas's isolated local n8n schedule after the Compose API is ready.

Secrets only enter an ignored temporary credential file; never command arguments.
"""

import json
import subprocess
from pathlib import Path
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
IMAGE = (
    "n8nio/n8n@sha256:87e0bab2c93192e8dd885ff7b0697c22a1bd97489568a8c67cc140fd7dbb342d"
)
NETWORK = "atlas-commercial-intelligence_default"
VOLUME = "atlas-n8n-data"


def main():
    folder = ROOT / ".runtime/n8n"
    folder.mkdir(parents=True, exist_ok=True)
    secret = dotenv_values(ROOT / ".env.compose")["API_KEY"]
    credentials = folder / "credentials.json"
    credentials.write_text(
        json.dumps(
            [
                {
                    "id": "atlasHeader",
                    "name": "Atlas local API",
                    "type": "httpHeaderAuth",
                    "data": {"name": "X-API-Key", "value": secret},
                }
            ]
        )
    )
    credentials.chmod(0o600)
    workflow = json.loads((ROOT / "workflows/weekly-review.n8n.json").read_text())
    workflow["id"] = "atlasWeeklySchedule"
    workflow["nodes"][1]["parameters"]["url"] = "http://api:8080/api/reports/weekly"
    workflow["nodes"][1]["credentials"] = {
        "httpHeaderAuth": {"id": "atlasHeader", "name": "Atlas local API"}
    }
    (folder / "workflow.json").write_text(json.dumps(workflow))
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                NETWORK,
                "-v",
                f"{folder}:/inputs:ro",
                "-v",
                f"{VOLUME}:/home/node/.n8n",
                "--entrypoint",
                "/bin/sh",
                IMAGE,
                "-c",
                "n8n import:credentials --input=/inputs/credentials.json && n8n import:workflow --input=/inputs/workflow.json && n8n publish:workflow --id=atlasWeeklySchedule",
            ],
            check=True,
        )
    finally:
        credentials.unlink(missing_ok=True)
    print(
        "Schedule published. Start the isolated n8n service using workflows/README.md."
    )


if __name__ == "__main__":
    main()
