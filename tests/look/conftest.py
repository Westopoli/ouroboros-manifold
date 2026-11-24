"""Shared fixtures for tests/look backends: a fake ollama server and a fake `claude`.

Assumed contract (the builder reads this, spec piece 2 leaves it open):
  check = {"name", "backend": "ollama"|"claude", "prompt": str,
           "truth": {"class": str} | {"count": int} | {"coordinates": [[x, y], ...]}}
  env OM_LOOK_OLLAMA_URL (base url), OM_LOOK_OLLAMA_MODEL, OM_LOOK_CACHE_DIR, OM_LOOK_TIMEOUT (seconds)
  ollama: POST {url}/api/generate {"model","prompt","images":[b64],"stream":false} -> {"response": text}
  answers: "class: X" | "count: N" | "coordinates: (x,y) (x,y)"
"""
import json
import os
import stat
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PNG_HEAD = b"\x89PNG\r\n\x1a\n"


def make_png(path, tag=b"CLEAN"):
    Path(path).write_bytes(PNG_HEAD + tag)
    return Path(path)


class FakeOllama:
    def __init__(self):
        self.requests = []
        self.reply = lambda req: "count: 0"
        self.status = 200
        self.delay = 0.0
        outer = self

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append({"path": self.path, "body": body})
                if outer.delay:
                    import time
                    time.sleep(outer.delay)
                text = outer.reply(body)
                data = json.dumps({"response": text, "done": True}).encode()
                self.send_response(outer.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.url = "http://127.0.0.1:%d" % self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def ollama(monkeypatch, tmp_path):
    srv = FakeOllama()
    monkeypatch.setenv("OM_LOOK_OLLAMA_URL", srv.url)
    monkeypatch.setenv("OM_LOOK_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("OM_LOOK_OLLAMA_MODEL", raising=False)
    yield srv
    srv.close()


FAKE_CLAUDE = """#!{py}
import json, os, sys, time
log = os.environ["FAKE_CLAUDE_LOG"]
with open(log, "a") as f:
    f.write(json.dumps({{"argv": sys.argv[1:], "pid": os.getpid(), "stdin": sys.stdin.read()}}) + "\\n")
mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
if mode == "sleep":
    time.sleep(30)
if mode == "fail":
    sys.stderr.write("boom")
    sys.exit(3)
sys.stdout.write(os.environ.get("FAKE_CLAUDE_OUT", "count: 0"))
"""


class FakeClaude:
    def __init__(self, tmp_path, monkeypatch):
        self.bin = tmp_path / "fakebin"
        self.bin.mkdir()
        exe = self.bin / "claude"
        exe.write_text(FAKE_CLAUDE.format(py=sys.executable))
        exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
        self.log = tmp_path / "claude.log"
        monkeypatch.setenv("PATH", str(self.bin) + os.pathsep + os.environ["PATH"])
        monkeypatch.setenv("FAKE_CLAUDE_LOG", str(self.log))
        monkeypatch.setenv("OM_LOOK_CACHE_DIR", str(tmp_path / "cache"))
        self.mp = monkeypatch

    def say(self, out, mode="ok"):
        self.mp.setenv("FAKE_CLAUDE_OUT", out)
        self.mp.setenv("FAKE_CLAUDE_MODE", mode)

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(l) for l in self.log.read_text().splitlines()]


@pytest.fixture
def claude(tmp_path, monkeypatch):
    return FakeClaude(tmp_path, monkeypatch)


def check(backend, truth=None, name="overlap", prompt="How many units overlap?"):
    return {"name": name, "backend": backend, "prompt": prompt,
            "truth": truth if truth is not None else {"count": 0}}
