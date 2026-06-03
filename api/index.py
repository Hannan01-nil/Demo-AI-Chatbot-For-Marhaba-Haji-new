import os
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

os.environ.setdefault("VERCEL", "1")

from backend.app import app as _backend_app


async def app(scope, receive, send):
    if scope["type"] != "http":
        await _backend_app(scope, receive, send)
        return
    path = scope.get("path", "")
    if path.startswith("/api"):
        scope = dict(scope)
        scope["path"] = path[4:] or "/"
        scope["root_path"] = ""
    await _backend_app(scope, receive, send)
