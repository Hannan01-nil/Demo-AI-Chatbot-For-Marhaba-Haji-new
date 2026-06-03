import os
import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import uvicorn

    FRONTEND = Path(__file__).resolve().parent / "public" / "index.html"
    PORT = 8000

    def _open_browser():
        import time
        time.sleep(2)
        url = FRONTEND.as_uri()
        print(f"  Opening {url}")
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()

    border = "=" * 50
    print(f"\n  {border}")
    print("    MARHABA HAJI CHATBOT")
    print(f"  {border}")
    print(f"  API:     http://localhost:{PORT}")
    print(f"  Docs:    http://localhost:{PORT}/docs")
    print(f"  Chatbot: {FRONTEND.as_uri()}")
    print(f"  {border}\n")
    print("  Press Ctrl+C to stop\n")

    os.environ.setdefault("VERCEL", "")
    uvicorn.run("backend.app:app", host="127.0.0.1", port=PORT, reload=True)
