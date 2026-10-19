"""Compare fresh live evaluation outputs; never reuse an earlier run's results."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-price", type=float)
    parser.add_argument("--output-price", type=float)
    args = parser.parse_args()
    summary = []
    with tempfile.TemporaryDirectory(prefix="atlas-eval-") as folder:
        for variant in ("baseline", "evidence"):
            output = Path(folder) / f"{variant}.json"
            command = [
                sys.executable,
                str(ROOT / "evals/run.py"),
                "--mode",
                "live",
                "--variant",
                variant,
                "--output",
                str(output),
            ]
            for name in ("input_price", "output_price"):
                if getattr(args, name) is not None:
                    command += ["--" + name.replace("_", "-"), str(getattr(args, name))]
            result = subprocess.run(command, cwd=ROOT)
            # Exit 1 can mean measured failures. A fresh result is required either way.
            if result.returncode not in (0, 1) or not output.exists():
                raise SystemExit(
                    f"{variant}: no fresh evaluation produced; comparison not updated."
                )
            data = json.loads(output.read_text())
            if data["mode"] != "live" or data["variant"] != variant:
                raise SystemExit("Evaluation provenance mismatch.")
            (ROOT / f"evals/results-live-{variant}.json").write_text(output.read_text())
            summary.append(
                {
                    key: data[key]
                    for key in (
                        "variant",
                        "model",
                        "benchmark_sha256",
                        "accuracy",
                        "refusal_recall",
                        "median_latency_ms",
                        "total_input_tokens",
                        "total_output_tokens",
                        "estimated_cost_usd",
                    )
                }
            )
            summary[-1]["failures"] = [r for r in data["results"] if not r["pass"]]
    if summary[0]["benchmark_sha256"] != summary[1]["benchmark_sha256"]:
        raise SystemExit("Cannot compare different benchmarks.")
    (ROOT / "evals/prompt-comparison.json").write_text(json.dumps(summary, indent=2))
    print("Saved both measured prompt results and failure cases.")


if __name__ == "__main__":
    main()
