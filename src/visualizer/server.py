"""
================================================================================
D3.JS SERVING CONTROLLER & ANALYTICS API BACKEND (REFACTORED)
================================================================================
Purpose:
  Provides high-speed REST endpoints querying the MartRepository
  and serves the bespoke D3.js executive dashboard with zero external dependencies.
Refactoring Highlights:
  - Strict separation of concerns (SoC): SQL queries delegated to `MartRepository`.
  - Robust MIME typing and Pathlib static asset serving.
  - Windows CP1252-safe console logging and graceful port binding.
================================================================================
"""

import os
import sys
import json
import mimetypes
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Ensure package root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PATHS, SERVER
from src.visualizer.repository import MartRepository

# Shared repository instance
REPO = MartRepository(PATHS.sqlite_db_path)

class AnalyticsAPIHandler(BaseHTTPRequestHandler):
    """HTTP Controller for serving analytics endpoints and static web assets."""

    def send_json(self, data, status: int = 200):
        body = json.dumps(data, default=lambda o: float(o) if hasattr(o, '__float__') else str(o)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # API Routes
        route_map = {
            "/api/kpis": lambda: self.send_json(REPO.get_executive_kpis()),
            "/api/sankey": lambda: self.send_json(REPO.get_sankey_flow()),
            "/api/rfm": lambda: self.send_json(REPO.get_rfm_segments()),
            "/api/monthly": lambda: self.send_json(REPO.get_monthly_trajectory()),
            "/api/categories": lambda: self.send_json(REPO.get_top_categories())
        }

        handler = route_map.get(self.path)
        if handler:
            handler()
        else:
            self.serve_static_asset()

    def serve_static_asset(self):
        url_path = self.path.split("?")[0]
        if url_path in ("/", ""):
            file_path = PATHS.web_dir / "index.html"
        else:
            file_path = PATHS.web_dir / url_path.lstrip("/")

        if not file_path.exists() or file_path.is_dir():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"

        with open(file_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

def start_server(port: int = None, host: str = None):
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

    bind_port = port or SERVER.default_port
    bind_host = host or SERVER.default_host
    server = ThreadingHTTPServer((bind_host, bind_port), AnalyticsAPIHandler)
    print("=" * 75)
    print(f"[*] [D3.JS ANALYTICS COCKPIT] Server live on http://localhost:{bind_port}")
    print("    Serving Enterprise Gold Mart & Interactive D3.js Visualizer")
    print("=" * 75)
    server.serve_forever()

if __name__ == "__main__":
    cli_port = int(sys.argv[1]) if len(sys.argv) > 1 else SERVER.default_port
    start_server(port=cli_port)
