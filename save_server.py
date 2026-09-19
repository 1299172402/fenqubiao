"""接收浏览器 POST 过来的 MHTML 内容并写入磁盘。

用法: python save_server.py [端口] [输出目录]
"""

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else r"d:\Documents\GitHub\fenqubiao\mhtml"
os.makedirs(OUTDIR, exist_ok=True)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        q = parse_qs(urlparse(self.path).query)
        name = (q.get("name") or ["unnamed"])[0]
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)

        path = os.path.join(OUTDIR, f"{name}.mhtml")
        with open(path, "wb") as f:
            f.write(body)

        msg = f"OK {path} {len(body)} bytes".encode()
        print(msg.decode(), flush=True)
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)

    def log_message(self, fmt, *args):
        pass


print(f"listening on 127.0.0.1:{PORT}, outdir={OUTDIR}", flush=True)
HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
