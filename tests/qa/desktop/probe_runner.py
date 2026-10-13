"""Runs one Godot probe script on a real display (Xvfb, software GL) and returns its results.

A probe (a SceneTree script under tests/qa/desktop/) prints one `RESULT {"check":..,"ok":..,"msg":..}`
line per named check. The desktop tests parametrise over the check names, so each check is its own
test id and a red one reports the probe's first failing assertion message.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

import pytest

from daemon_client import REPO_ROOT, find_godot

XVFB_SCREEN = "1920x1080x24"


def run_probe(script: str, timeout: int = 150) -> dict[str, dict]:
    scratch = Path(tempfile.mkdtemp(prefix="qa_probe."))
    try:
        (scratch / "saves").mkdir()
        (scratch / "xdg" / "data").mkdir(parents=True)
        env = dict(os.environ)
        for var in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
            env.pop(var, None)
        env["XDG_DATA_HOME"] = str(scratch / "xdg")
        env["OM_SAVE_DIR"] = str(scratch / "saves")
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        env["GALLIUM_DRIVER"] = "llvmpipe"
        cmd = [
            "xvfb-run", "-a", "-s", "-screen 0 %s" % XVFB_SCREEN,
            find_godot(), "--path", str(REPO_ROOT),
            "--display-driver", "x11", "--rendering-driver", "opengl3",
            "--quit-after", "20000", "--script", script,
        ]
        proc = subprocess.Popen(cmd, cwd=str(scratch), env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, start_new_session=True, text=True)
        try:
            out, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            out, _ = proc.communicate()
            pytest.fail("probe %s timed out:\n%s" % (script, out[-800:]))
        finally:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        results = {}
        for line in out.splitlines():
            if line.startswith("RESULT "):
                row = json.loads(line[7:])
                results[row["check"]] = row
        if not results:
            pytest.fail("no RESULT lines from %s:\n%s" % (script, out[-1200:]))
        return results
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
