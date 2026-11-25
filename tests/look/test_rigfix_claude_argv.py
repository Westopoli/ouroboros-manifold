"""look-judge-rig fixes, defect 1 (docs/reports/2026-11-24-look-judge-rig-status.md; measurement 2026-11-24): `_ask_claude` puts the prompt after the variadic
`--allowedTools Read`, so the real `claude -p` swallows the prompt as a tool name, sees no prompt, and exits 1 on every call: every claude verdict was UNSURE and the
calibration "0 false passes" meant nothing. Spec piece 2: "headless `claude -p`; the image reaches the process; one image per call".

The fake `claude` here is strict like the real one: tokens after a variadic flag (`--allowedTools`, ...) up to the next dash-token are that flag's values, not the
prompt; the prompt is a positional before the variadic flag, after `--`, or on stdin; no prompt -> exit 1 with the real error text.
"""
import json
import os
import stat
import subprocess
import sys

import pytest

from conftest import check, make_png

STRICT = """#!{py}
import json, os, sys
argv = sys.argv[1:]
VARIADIC = {{"--allowedTools", "--allowed-tools", "--disallowedTools", "--disallowed-tools", "--tools", "--add-dir", "--mcp-config"}}
pos, taken, i = [], [], 0
while i < len(argv):
    a = argv[i]
    if a == "--":
        pos += argv[i + 1:]
        break
    if a in VARIADIC:
        i += 1
        while i < len(argv) and not argv[i].startswith("-"):
            taken.append(argv[i])
            i += 1
        continue
    if a.startswith("-"):
        i += 1
        continue
    pos.append(a)
    i += 1
stdin = sys.stdin.read()
prompt = "\\n".join(pos) if pos else stdin
with open(os.environ["FAKE_CLAUDE_LOG"], "a") as f:
    f.write(json.dumps({{"argv": argv, "prompt": prompt, "allowed": taken}}) + "\\n")
if not prompt.strip():
    sys.stderr.write("Error: Input must be provided either through stdin or as a prompt argument when using --print\\n")
    sys.exit(1)
sys.stdout.write("count: 0")
"""


@pytest.fixture
def strict(tmp_path, monkeypatch):
    b = tmp_path / "strictbin"
    b.mkdir()
    exe = b / "claude"
    exe.write_text(STRICT.format(py=sys.executable))
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
    log = tmp_path / "strict.log"
    monkeypatch.setenv("PATH", str(b) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(log))
    monkeypatch.setenv("OM_LOOK_CACHE_DIR", str(tmp_path / "cache"))
    return log


def _run(*argv):
    return subprocess.run(["claude", *argv], input="", capture_output=True, text=True)


def test_control_strict_fake_models_the_real_cli(strict):
    """Positive control (spec piece 2), green today: the strict fake accepts a standalone prompt before the variadic flag and exits 1 on today's argv shape
    (prompt after `--allowedTools Read`), so a red below is the back end's argv and not the harness."""
    assert _run("-p", "hello", "--allowedTools", "Read").returncode == 0
    r = _run("-p", "--allowedTools", "Read", "hello")
    assert r.returncode == 1 and "Input must be provided" in r.stderr


def test_claude_backend_prompt_is_not_swallowed_by_the_variadic_flag(strict, tmp_path):
    """Spec piece 2 "headless `claude -p`; the image reaches the process": judge(png, claude check) against the strict fake must get an answer (count 0 == truth 0 -> PASS),
    not exit 1 -> UNSURE; the prompt the fake received names the image file, and Read stays allowed so the model can open it."""
    png = make_png(tmp_path / "crop.png")
    out = check("claude", {"count": 0})
    from scripts.look.backends import judge
    res = judge(png, out)
    assert res["verdict"] == "PASS", "claude exited nonzero: %r" % res["raw"]
    calls = [json.loads(l) for l in strict.read_text().splitlines()]
    assert len(calls) == 1
    assert str(png) in calls[0]["prompt"]
    assert "Read" in calls[0]["allowed"]
