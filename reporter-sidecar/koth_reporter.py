#!/usr/bin/env python3
"""
Minimal always-on KotH tag reporter -- runs ONLY in this isolated sidecar,
never inside a machine a player can compromise. Serves whatever is
currently written to TAG_PATH (a volume shared with the paired vulnbox)
on GET /tag. Read-only: this process never accepts writes itself.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

TAG_PATH = os.environ.get("KOTH_TAG_PATH", "/opt/koth/tag")
PORT = int(os.environ.get("KOTH_REPORTER_PORT", "9001"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/tag":
            self.send_response(404)
            self.end_headers()
            return
        try:
            with open(TAG_PATH) as f:
                tag = f.read().strip()
        except OSError:
            tag = "unclaimed"
        body = tag.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
