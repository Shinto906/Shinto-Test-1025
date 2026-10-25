"""Minimal stand-in for a cloud instance metadata service (IMDS).

Only reachable from inside the Docker network. Used to demonstrate an
SSRF -> internal credential disclosure chain without any real cloud account.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

ROLE_NAME = "ledgervault-provisioner"
BOOTSTRAP_TOKEN = os.getenv("BOOTSTRAP_TOKEN", "bootstrap-provisioning-7f3a")

CREDENTIALS = {
    "Code": "Success",
    "Type": "AWS-HMAC",
    "AccessKeyId": "ASIAEXAMPLEINTERNAL",
    "SecretAccessKey": "wJalrXUtnFEMIexampleKEYinternal",
    "Token": "FwoGZXIvYXdzEXAMPLEsessiontoken",
    "BootstrapToken": BOOTSTRAP_TOKEN,
    "Expiration": "2030-01-01T00:00:00Z",
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, code: int = 200, ctype: str = "text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Server", "EC2ws")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        path = self.path.rstrip("/")
        if path == "/latest/meta-data/iam/security-credentials":
            self._send(ROLE_NAME)
        elif path == f"/latest/meta-data/iam/security-credentials/{ROLE_NAME}":
            self._send(json.dumps(CREDENTIALS, indent=2), ctype="application/json")
        elif path == "/latest/meta-data":
            self._send("iam/\nhostname\ninstance-id\n")
        elif path in ("", "/latest"):
            self._send("meta-data/\n")
        else:
            self._send("Not Found", code=404)

    def log_message(self, *args):
        return


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 80), Handler).serve_forever()
