# spec: docs/stories/H-077.md (mail-and-station), Tests 10; rule 3 of docs/method/communication.md
"""H-077 .claude/hooks/mail-guard.sh. Rule: "No chat is pushed a message." PreToolUse hook on `SendMessage`: allows
`to` equal to `main` or a sub-agent id (`^a[0-9a-f]{8,}`), denies the rest with
`denied: cross-chat messages go through scripts/method/mail.py send (docs/method/communication.md)`.
Input is the PreToolUse JSON `{"tool_name": "SendMessage", "tool_input": {"to": ...}}` as .claude/hooks/git-guard.sh
reads it; the deny form is permissionDecision=deny with the text as its reason (git-guard's form).
Control (green today): git-guard.sh denies a destructive command with the same input shape, so the harness works."""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
HOOK = REPO / ".claude" / "hooks" / "mail-guard.sh"
DENY = "denied: cross-chat messages go through scripts/method/mail.py send (docs/method/communication.md)"
DESTRUCTIVE = "git re" + "set --hard"


def run(path, tool_input, tool="SendMessage"):
    return subprocess.run(["bash", str(path)], input=json.dumps({"tool_name": tool, "tool_input": tool_input}),
                          capture_output=True, text=True, timeout=30)


def test_control_git_guard_denies_with_the_same_input_shape():
    r = run(REPO / ".claude" / "hooks" / "git-guard.sh", {"command": DESTRUCTIVE}, tool="Bash")
    assert "permissionDecision" in r.stdout and "deny" in r.stdout


def test_t0_hook_exists():
    assert HOOK.exists(), f"{HOOK} missing"


def test_t10_cross_chat_names_are_denied_with_the_exact_text():
    """H-077 Tests 10: the hook denies `{"to": "ouroboros-manifold-90 [8a69cc]"}` and `{"to": "beta-staircase-gate-channel"}`
    with the exact text."""
    for to in ("ouroboros-manifold-90 [8a69cc]", "beta-staircase-gate-channel"):
        r = run(HOOK, {"to": to, "message": "hi"})
        assert "deny" in r.stdout and DENY in r.stdout, (to, r.stdout, r.stderr)


def test_t10_main_and_sub_agent_ids_are_allowed():
    """H-077 Tests 10: allows `{"to": "main"}` and `{"to": "a93eaf778770b83ac"}`."""
    for to in ("main", "a93eaf778770b83ac"):
        r = run(HOOK, {"to": to, "message": "hi"})
        assert r.returncode == 0 and "deny" not in r.stdout and DENY not in r.stdout, (to, r.stdout, r.stderr)
