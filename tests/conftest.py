import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

# Robots fixture: GPTBot is blocked from everything, everyone else
# may fetch / (no specific group -> the * group only disallows
# /private/). The test server 403s GPTBot at the HTTP layer too,
# but lets CCBot through even though robots.txt blocks it from
# /private/ only -- and it 403s Bytespider, which robots.txt
# allows, to produce a genuine mismatch.
ROBOTS = """\
# test fixture
User-agent: GPTBot
Disallow: /

User-agent: CCBot
Disallow: /private/

User-agent: *
Disallow: /private/
Allow: /
"""

BLOCKED_UAS = ("GPTBot", "Bytespider")


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep test output clean
        pass

    def do_GET(self):
        ua = self.headers.get("User-Agent", "")
        if self.path == "/robots.txt":
            body = ROBOTS.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if any(token in ua for token in BLOCKED_UAS):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"forbidden")
            return
        body = b"<html><title>fixture</title>ok</html>"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture()
def local_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
