"""Run the bot without FastAPI, PostgreSQL or MinIO."""
import os
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / ".local-python"))
for line in (root / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
os.environ["BACKEND_ENABLED"] = "false"
url = os.environ.get("WEBAPP_URL", "")
if not url.startswith("https://") or "your-domain" in url:
    raise SystemExit("Set WEBAPP_URL in .env to the HTTPS URL printed by cloudflared first.")
runpy.run_path(str(root / "bot" / "bot.py"), run_name="__main__")
