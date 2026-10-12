"""SV-1: the sim viewer's client for the pipe (docs/northstar/plans/2026-10-12-simviewer-spec.md).

Frames are a 4-byte big-endian length then a JSON body, both ways; the server
writes `hello` first (spec pre-flight 1). `send` returns the frames a verb
answers, up to its terminal frame (pre-flight 2).
"""
import json
import subprocess
from pathlib import Path

PIPE_DBG = Path(__file__).resolve().parents[2] / "pipe" / "ouroboros_pipe_dbg"

# autoload/c_bridge.gd:27
DEFAULT_FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
# autoload/c_bridge.gd:749
JUMP_TICKS = 50

# Verb -> frame types it answers, in order (docs/architecture.md, set_seed and
# session commands). `step` is handled by count; `run_to` streams a variable
# number of deltas and has no row.
TERMINAL = {
    "set_seed": [],
    "snapshot": ["snapshot"],
    "mission_start": ["mission"],
    "mission_begin": ["tactical"],
    "objective_complete": ["ack"],
    "mission_end": ["debrief", "snapshot"],
    "mission_refuse": ["debrief", "snapshot"],
    "jump": ["chronicle", "snapshot"],
    "save": ["ack"],
    "load": ["snapshot"],
    "set_feature": ["ack"],
}


class PipeError(Exception):
    def __init__(self, frame):
        super().__init__(frame)
        self.frame = frame


class PipeSession:
    def __init__(self, argv=None):
        self._proc = subprocess.Popen(
            argv or [str(PIPE_DBG)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self._closed = False
        self.hello = self._read()

    def _read_exactly(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self._proc.stdout.read(n - len(buf))
            if not chunk:
                raise EOFError("pipe closed")
            buf += chunk
        return buf

    def _read(self):
        size = int.from_bytes(self._read_exactly(4), "big")
        return json.loads(self._read_exactly(size))

    def _write(self, obj):
        body = json.dumps(obj).encode()
        self._proc.stdin.write(len(body).to_bytes(4, "big") + body)
        self._proc.stdin.flush()

    def send(self, name, **fields):
        if name == "step":
            types = ["delta"] * fields.get("n", 1) + ["ack"]
        elif name in TERMINAL:
            types = TERMINAL[name]
        else:
            raise ValueError("no terminal frame known for %s" % name)
        self._write({"type": "cmd", "name": name, **fields})
        frames = []
        for _ in types:
            frame = self._read()
            if frame.get("type") == "error":
                raise PipeError(frame)
            frames.append(frame)
        return frames

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self._write({"type": "cmd", "name": "quit"})
            self._proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait()
        self._proc.stdout.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
