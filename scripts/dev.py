"""Start both local services with server-only credentials; stop if either exits."""

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
env = {
    **os.environ,
    **{k: v for k, v in dotenv_values(root / ".env").items() if v is not None},
}
env["PYTHONPATH"] = str(root / "services/api")
# An explicit runtime directory avoids accidentally selecting a Rosetta Node.
if env.get("ATLAS_NODE_BIN"):
    env["PATH"] = env["ATLAS_NODE_BIN"] + os.pathsep + env.get("PATH", "")
if not shutil.which("npm", path=env.get("PATH")):
    raise SystemExit(
        "npm was not found. Install Node and set ATLAS_NODE_BIN to its bin directory."
    )
children = []


def stop(*args):
    for process in children:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
    for process in children:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def interrupted(*args):
    raise KeyboardInterrupt


signal.signal(signal.SIGINT, interrupted)
signal.signal(signal.SIGTERM, interrupted)
try:
    children.append(
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "ciq.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8031",
            ],
            cwd=root,
            env=env,
            start_new_session=True,
        )
    )
    children.append(
        subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=root / "apps/web",
            env=env,
            start_new_session=True,
        )
    )
    print("Atlas: http://127.0.0.1:3031", flush=True)
    while all(process.poll() is None for process in children):
        time.sleep(0.25)
    failed = next(process for process in children if process.poll() is not None)
    raise SystemExit(failed.returncode or 1)
except KeyboardInterrupt:
    pass
finally:
    stop()
