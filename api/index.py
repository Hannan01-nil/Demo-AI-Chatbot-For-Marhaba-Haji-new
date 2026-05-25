import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

for path in (PROJECT_ROOT, BACKEND_DIR):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

os.environ.setdefault("VERCEL", "1")

from app import app as backend_app  # noqa: E402


async def app(scope, receive, send):
    """Vercel routes requests through /api; the backend keeps clean root paths."""
    if scope["type"] == "http" and scope.get("path", "").startswith("/api"):
        scope = dict(scope)
        scope["path"] = scope["path"][4:] or "/"
        scope["root_path"] = ""
    await backend_app(scope, receive, send)
