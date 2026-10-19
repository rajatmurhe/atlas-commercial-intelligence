"""Generate separate Docker credentials; never overwrite an existing file."""

from pathlib import Path
import secrets

p = Path(__file__).resolve().parents[1] / ".env.compose"
with p.open("x") as f:
    for name in ["POSTGRES_PASSWORD", "APP_PASSWORD", "READER_PASSWORD", "API_KEY"]:
        f.write(f"{name}={secrets.token_urlsafe(32)}\n")
p.chmod(0o600)
print(
    "Created .env.compose. Start with: docker compose --env-file .env.compose up --build"
)
