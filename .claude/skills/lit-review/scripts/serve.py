#!/usr/bin/env python3
"""serve.py — serve a review folder over localhost AND accept decision saves.

Why a server: a file:// page can't write to disk, and the File System Access picker defaults to
Downloads. Serving over localhost lets the review page POST its decisions back and we write
decisions.json straight into the review folder — true one-click autosave, no picker.

Endpoints:
  GET  /<file>                     → serve files from --dir (the review folder)
  POST /save?name=decisions.json   → write the JSON body into --dir/<name> (name sanitised)

Usage:  serve.py --dir <review-folder> [--port 8765]
Prints the OPEN url. Runs until Ctrl-C. Bind 127.0.0.1 only. Run in the BACKGROUND.
"""
import argparse, http.server, functools, socketserver, socket, sys, json, re
from pathlib import Path

class Handler(http.server.SimpleHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.split("?")[0] != "/save":
            return self._send(404, {"error": "unknown endpoint"})
        # sanitise name → basename, json only
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        name = (qs.get("name", ["decisions.json"])[0])
        name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name) or "decisions.json"
        if not name.endswith(".json"): name += ".json"
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            json.loads(raw)  # validate it's JSON
        except Exception as e:
            return self._send(400, {"error": f"invalid json: {e}"})
        dest = Path(self.directory) / name
        dest.write_bytes(raw)
        sys.stderr.write(f"[save] wrote {dest} ({len(raw)} bytes)\n"); sys.stderr.flush()
        return self._send(200, {"ok": True, "path": str(dest), "bytes": len(raw)})

    def end_headers(self):
        # allow the served page to POST back
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, *a):  # quieter
        pass

def free_port(preferred):
    for p in [preferred, 0]:
        try:
            s = socket.socket(); s.bind(("127.0.0.1", p)); port = s.getsockname()[1]; s.close(); return port
        except OSError:
            continue
    return preferred

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    d = Path(a.dir).resolve()
    if not d.is_dir(): sys.exit(f"not a directory: {d}")
    port = free_port(a.port)
    handler = functools.partial(Handler, directory=str(d))
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        base = f"http://127.0.0.1:{port}/"
        print(f"serving {d} at {base}")
        for h in sorted(p.name for p in d.glob("*.html")):
            print(f"OPEN: {base}{h}")
        sys.stdout.flush()
        httpd.serve_forever()

if __name__ == "__main__":
    main()
