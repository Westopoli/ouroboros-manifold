"""Interactive pipe driver for the long-mission suite (see README.md)."""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
N_REGIONS = 80
ARCHETYPES = ["defensive_stand", "siege_breaking", "reconquest", "assault", "suppression",
              "multi_front_defense", "interception", "evacuation", "containment",
              "counterinsurgency"]


class Pipe:
    def __init__(self):
        self.p = subprocess.Popen([str(PIPE)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.hello = self._read()

    def _read(self):
        h = self.p.stdout.read(4)
        if len(h) < 4:
            raise EOFError("pipe closed")
        return json.loads(self.p.stdout.read(int.from_bytes(h, "big")))

    def cmd(self, name, **kw):
        """Send one cmd, read nothing (set_seed answers no frame on success)."""
        body = json.dumps({"type": "cmd", "name": name, **kw}).encode()
        self.p.stdin.write(len(body).to_bytes(4, "big") + body)
        self.p.stdin.flush()

    def send(self, name, **kw):
        """Send one cmd; return the first reply frame. Two-frame replies
        (jump: chronicle then snapshot) use read_more() for the second."""
        self.cmd(name, **kw)
        return self._read()

    def read_more(self):
        return self._read()

    def close(self):
        try:
            self.p.stdin.write((len(b'{"type":"cmd","name":"quit"}')).to_bytes(4, "big") + b'{"type":"cmd","name":"quit"}')
            self.p.stdin.flush()
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()


def first_mission(seed):
    """(archetype, deadline_ticks) of the seed's first mission, read cheaply."""
    pp = Pipe()
    try:
        pp.cmd("set_seed", seed=seed, n_regions=N_REGIONS, features=FEATURES)
        m = pp.send("mission_start", faction=0)
        return (m.get("archetype"), m.get("deadline_ticks")) if m["type"] == "mission" else (None, m)
    finally:
        pp.close()
