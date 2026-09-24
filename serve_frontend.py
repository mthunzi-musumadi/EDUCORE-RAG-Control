"""
==============================================================================
EDUCORE SERVICES ENTERPRISE FRONTEND SERVER (PORT 3000)
Decoupled, zero-dependency static server with reverse proxy to port 8000 backend.
Compliant with ISO/IEC 42001:2023 & Zambian Data Protection Act No. 3
==============================================================================
"""

import os
import sys
import json
import mimetypes
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Default configurations
DEFAULT_PORT = 3000
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")

class EducoreFrontendHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Suppress verbose asset logging, keep errors and API requests
        if self.path.startswith(("/v1", "/api", "/health")):
            sys.stdout.write(f"[Proxy] {self.command} {self.path} -> {args[1]}\n")
            sys.stdout.flush()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Connection", "close")
        self.end_headers()

    def proxy_to_backend(self):
        target_url = f"{BACKEND_URL}{self.path}"
        headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ("host", "content-length", "connection"):
                headers[k] = v
        headers["Connection"] = "close"

        body = None
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length)

        req = urllib.request.Request(target_url, data=body, headers=headers, method=self.command)

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                is_sse = "text/event-stream" in resp.headers.get("Content-Type", "")
                if is_sse:
                    self.send_response(resp.status)
                    for header, val in resp.getheaders():
                        if header.lower() not in ("transfer-encoding", "content-encoding", "connection"):
                            self.send_header(header, val)
                    self.send_header("Connection", "close")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    while True:
                        line = resp.readline()
                        if not line:
                            break
                        self.wfile.write(line)
                        self.wfile.flush()
                else:
                    resp_body = resp.read()
                    self.send_response(resp.status)
                    for header, val in resp.getheaders():
                        if header.lower() not in ("transfer-encoding", "content-encoding", "content-length", "connection"):
                            self.send_header(header, val)
                    self.send_header("Content-Length", str(len(resp_body)))
                    self.send_header("Connection", "close")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(resp_body)
                    self.wfile.flush()
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(err_body)))
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_body)
            self.wfile.flush()
        except Exception as e:
            err_msg = json.dumps({"error": f"Backend unreachable: {str(e)}"}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(err_msg)))
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_msg)
            self.wfile.flush()

    def serve_static(self):
        # Normalize requested path
        path = self.path.split("?")[0].lstrip("/")
        if not path:
            path = "index.html"

        file_path = os.path.join(DIST_DIR, path)

        # SPA fallback: if file does not exist, serve index.html
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(DIST_DIR, "index.html")

        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Frontend not built. Please run: cd frontend && npm run build")
            return

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            if path.startswith("assets/"):
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            else:
                self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def do_GET(self):
        if self.path.startswith(("/v1", "/api", "/health")):
            self.proxy_to_backend()
        else:
            self.serve_static()

    def do_POST(self):
        if self.path.startswith(("/v1", "/api", "/health")):
            self.proxy_to_backend()
        else:
            self.send_response(405)
            self.end_headers()

    def do_DELETE(self):
        if self.path.startswith(("/v1", "/api", "/health")):
            self.proxy_to_backend()
        else:
            self.send_response(405)
            self.end_headers()

    def do_PUT(self):
        if self.path.startswith(("/v1", "/api", "/health")):
            self.proxy_to_backend()
        else:
            self.send_response(405)
            self.end_headers()

def run_server(port: int = DEFAULT_PORT):
    if not os.path.exists(DIST_DIR):
        print(f"Warning: {DIST_DIR} not found. Attempting to build frontend...")
        os.system(f"cd /d \"{os.path.join(BASE_DIR, 'frontend')}\" && npm run build")

    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, EducoreFrontendHandler)
    print("=" * 70)
    print("  EDUCORE SERVICES ENTERPRISE FRONTEND ONLINE")
    print(f"  Interface: http://localhost:{port}")
    print(f"  Serving:   {DIST_DIR}")
    print(f"  Backend:   {BACKEND_URL}")
    print("=" * 70)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping frontend server...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    run_server(port)
