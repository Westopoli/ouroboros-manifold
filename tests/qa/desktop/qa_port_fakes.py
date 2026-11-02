"""Hermetic fakes for tests/qa/desktop/test_qa_port_unique.py (H-066): a fake
`godot` and `xvfb-run` on PATH, so GodotGame launches a scripted process instead
of the real game, and a decoy foreign listener in its own session.

Per-launch behaviour comes from FAKE_GODOT_PLAN (comma list, one mode per
launch, last repeats) and FAKE_GODOT_STATE (a dir holding launches.log and
decoys.log). Modes: listen, never, decoy, cannot_listen_alive,
cannot_listen_exit, early_exit.
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

FAKE_GODOT = r'''#!%(py)s
import os, socket, subprocess, sys, time
state = os.environ["FAKE_GODOT_STATE"]
plan = os.environ["FAKE_GODOT_PLAN"].split(",")
a = sys.argv
port = int(a[a.index("--qa-port") + 1])
log = os.path.join(state, "launches.log")
idx = len(open(log).read().splitlines()) if os.path.exists(log) else 0
mode = plan[min(idx, len(plan) - 1)]
with open(log, "a") as f:
    f.write("%%d %%d %%s\n" %% (port, os.getpid(), mode))
if mode == "early_exit":
    sys.exit(1)
if mode == "cannot_listen_exit":
    sys.stderr.write("qa_daemon: cannot listen on 127.0.0.1:%%d (err 22)\n" %% port)
    sys.stderr.flush()
    sys.exit(1)
if mode == "cannot_listen_alive":
    sys.stderr.write("qa_daemon: cannot listen on 127.0.0.1:%%d (err 22)\n" %% port)
    sys.stderr.flush()
    time.sleep(3600)
if mode == "never":
    time.sleep(3600)
if mode == "decoy":
    p = subprocess.Popen([sys.executable, %(decoy)r, str(port)], start_new_session=True)
    with open(os.path.join(state, "decoys.log"), "a") as f:
        f.write("%%d %%d\n" %% (port, p.pid))
    t = time.monotonic() + 10
    while time.monotonic() < t:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)
    time.sleep(3600)
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", port))
s.listen(8)
while True:
    c, _ = s.accept()
    c.close()
'''

DECOY = r'''import socket, sys, time
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", int(sys.argv[1])))
s.listen(8)
while True:
    c, _ = s.accept()
    c.close()
'''

FAKE_XVFB = '#!/bin/sh\nwhile [ "$1" != godot ]; do shift; done\nexec "$@"\n'


def install(bin_dir: Path) -> None:
    """Writes bin_dir/godot, bin_dir/xvfb-run and bin_dir/decoy.py."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    decoy = bin_dir / "decoy.py"
    decoy.write_text(DECOY)
    for name, text in (("godot", FAKE_GODOT % {"py": sys.executable, "decoy": str(decoy)}),
                       ("xvfb-run", FAKE_XVFB)):
        p = bin_dir / name
        p.write_text(text)
        p.chmod(p.stat().st_mode | stat.S_IXUSR)


def launches(state: Path) -> list[tuple[int, int, str]]:
    log = state / "launches.log"
    if not log.exists():
        return []
    out = []
    for line in log.read_text().splitlines():
        port, pid, mode = line.split()
        out.append((int(port), int(pid), mode))
    return out


def decoy_pids(state: Path) -> list[int]:
    log = state / "decoys.log"
    return [int(l.split()[1]) for l in log.read_text().splitlines()] if log.exists() else []


def alive(pid: int) -> bool:
    try:
        st = Path("/proc/%d/stat" % pid).read_text().rsplit(")", 1)[1].split()[0]
    except (FileNotFoundError, ProcessLookupError):
        return False
    return st != "Z"


def kill_group(pid: int) -> None:
    import signal
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
