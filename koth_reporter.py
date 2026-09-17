#!/usr/bin/env python3
"""
Minimal always-on KotH tag reporter.

Serves whatever is currently written to TAG_PATH on GET /tag. It does NOT
accept writes itself -- claiming a machine happens through whatever access
the machine's real vulnerability grants (webshell, SQLi file write, SSH
shell, etc.), by writing your team's token into TAG_PATH. Keeping this
reporter dependency-free and read-only means it adds no attack surface of
its own, and it stays up even if the "real" vulnerable service (Apache,
Tomcat, whatever) is patched, restarted, or crashes.
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
        pass  # keep container logs quiet


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
