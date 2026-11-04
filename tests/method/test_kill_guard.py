# Rule pins: R-990-01@?
"""H-081 tests (kill-guard hook). Story: docs/stories/H-081.md, Interfaces: "denies a command whose segments start
with `kill`, `pkill`, `killall`, or `fuser -k`, with `denied: processes are killed through scripts/method/proc.py
reap (docs/stories/H-081.md)`; allows `proc.py reap`."
The hook is fed PreToolUse JSON on stdin (as .claude/hooks/git-guard.sh is); a deny prints JSON with
permissionDecision deny, an allow prints nothing and exits 0.
"""
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOK = REPO / ".claude" / "hooks" / "kill-guard.sh"
GIT_GUARD = REPO / ".claude" / "hooks" / "git-guard.sh"
REASON = "denied: processes are killed through scripts/method/proc.py reap (docs/stories/H-081.md)"


def _run(hook, cmd):
    return subprocess.run(["bash", str(hook)], input=json.dumps({"tool_input": {"command": cmd}}),
                          capture_output=True, text=True, timeout=30)


def test_control_git_guard_does_not_stop_kill():
    """Positive control (green today): the harness feeds a hook and git-guard allows `kill -9 1234` (why the new hook is needed)."""
    r = _run(GIT_GUARD, "kill -9 1234")
    assert r.returncode == 0 and "deny" not in r.stdout


@pytest.mark.parametrize("cmd", ["kill -9 1234", "pkill godot", "fuser -k 8080/tcp", "sleep 1; killall x"])
def test_denies_kill_family(cmd):
    """S-H-081 test 5: the four kill forms are denied with the story's reason."""
    r = _run(HOOK, cmd)  # red: .claude/hooks/kill-guard.sh does not exist
    out = json.loads(r.stdout)["hookSpecificOutput"]
    assert out["permissionDecision"] == "deny" and REASON in out["permissionDecisionReason"]


@pytest.mark.parametrize("cmd", ["python3 scripts/method/proc.py reap", "grep 'pkill godot' notes.md"])
def test_allows_reap_and_quoted_kill_words(cmd):
    """S-H-081 test 5: proc.py reap and a quoted `pkill` argument of grep pass."""
    r = _run(HOOK, cmd)
    assert r.returncode == 0 and r.stdout.strip() == ""
