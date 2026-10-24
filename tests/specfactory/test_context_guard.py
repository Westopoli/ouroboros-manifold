# spec: docs/northstar/plans/2026-10-19-harness-enforcement-spec.md "### HARNESS-context-guard, the 400k hard stop" (Tests first)
# Rule pins: R-990-01@?
"""Context guard hook: .claude/hooks/context_guard.py over synthetic transcripts.

UNSTATED INTERFACE choices (the builder implements exactly these):
- "Silent" on exit 0 means stdout is empty and stderr holds no "CONTEXT GUARD" text (the NOT BUILT stub writes to stderr and must stay green on the pass tests).
- With no --transcript option the hook reads the stdin JSON; with options it ignores stdin (tests pass no stdin then).
- --prompt and --tool-input are plain strings; --tool-input is a JSON object text with `file_path` for Write/Edit.
- With --tool <name> the event is a tool event; with --prompt (and no --tool) it is a prompt event; stdin JSON decides by hook_event_name.
- The blocked prompt line and the tool line each start with `CONTEXT GUARD <n>k past <threshold>k:` on stderr, one line, and stdout is empty on exit 2.
- <threshold>k is the threshold in tokens divided by 1000, rounded down, as an integer (--threshold 1000 prints `1k`).
- The word match is case-insensitive whole-word: `Handoff:` passes; `handoffs` and `hand-off` do not.
- --memory-dir replaces ~/.claude/projects/ for the Write/Edit allowance; a path under it (after realpath) passes, even when the file does not exist yet.
- A missing --memory-dir defaults to ~/.claude/projects/.
- The tail read must not parse a line that was cut by the tail window; a window that is all unparseable text means no qualifying entry (exit 0).
- Test 10 reads .claude/settings.json: top-level "autoCompactWindow": 200000 and a hooks.UserPromptSubmit entry whose hooks[].command contains context_guard.py.
"""
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
HOOK = REPO / ".claude" / "hooks" / "context_guard.py"
SETTINGS = REPO / ".claude" / "settings.json"
SONNET = "claude-sonnet-5-5"

_clock = itertools.count()


def assistant(ctx, sidechain=False):
    n = next(_clock)
    return {"type": "assistant", "isSidechain": sidechain,
            "timestamp": f"2026-10-24T10:{n // 60:02d}:{n % 60:02d}.000Z",
            "message": {"model": SONNET,
                        "usage": {"input_tokens": 1000, "cache_read_input_tokens": ctx - 1500,
                                  "cache_creation_input_tokens": 500},
                        "content": [{"type": "text", "text": "ok"}]}}


def write_transcript(tmp_path, entries, extra_lines=(), name="t.jsonl"):
    p = tmp_path / name
    p.write_text("\n".join([json.dumps(e) for e in entries] + list(extra_lines)) + "\n")
    return p


def run(args=(), stdin=""):
    return subprocess.run([sys.executable, str(HOOK), *args], input=stdin, capture_output=True, text=True, timeout=30)


def prompt_json(transcript, prompt):
    return json.dumps({"hook_event_name": "UserPromptSubmit", "transcript_path": str(transcript),
                       "prompt": prompt, "session_id": "t"})


def tool_json(transcript, name, tool_input):
    return json.dumps({"hook_event_name": "PreToolUse", "transcript_path": str(transcript),
                       "tool_name": name, "tool_input": tool_input, "session_id": "t"})


def assert_silent_pass(r, why):
    assert r.returncode == 0, f"{why}: exit {r.returncode}, stderr {r.stderr!r}"
    assert r.stdout == "", f"{why}: stdout must be empty, got {r.stdout!r}"
    assert "CONTEXT GUARD" not in r.stderr, f"{why}: stderr must carry no guard line, got {r.stderr!r}"


def test_01_under_the_threshold_passes_silently(tmp_path):
    t = write_transcript(tmp_path, [assistant(399000)])
    assert_silent_pass(run(["--transcript", str(t), "--prompt", "continue"]), "399k is under 400k")


def test_02_blocks_a_prompt_past_the_threshold_with_the_guard_line(tmp_path):
    t = write_transcript(tmp_path, [assistant(450000)])
    r = run(stdin=prompt_json(t, "continue"))
    assert r.returncode == 2, f"Westley 2026-10-24 'go ahead with all 3, send it a message': I chose 400k, not 200k: a 450k prompt must exit 2, got {r.returncode}"
    assert r.stderr.startswith("CONTEXT GUARD 450k past 440k:"), r.stderr
    assert r.stdout == "", r.stdout


def test_03_the_word_in_another_case_lets_the_handoff_turn_through(tmp_path):
    t = write_transcript(tmp_path, [assistant(450000)])
    r = run(["--transcript", str(t), "--prompt", "Handoff: write the memory"])
    assert r.returncode == 0, f"exit {r.returncode}, stderr {r.stderr!r}"
    assert r.stdout.startswith("CONTEXT GUARD handoff turn allowed at 450k:"), r.stdout
    assert "CONTEXT GUARD" not in r.stderr, r.stderr


def test_04_the_word_as_a_substring_does_not_pass(tmp_path):
    t = write_transcript(tmp_path, [assistant(450000)])
    for prompt in ("write the handoffs", "do a hand-off now"):
        r = run(["--transcript", str(t), "--prompt", prompt])
        assert r.returncode == 2, f"{prompt!r} must still block, exit {r.returncode}"
        assert r.stderr.startswith("CONTEXT GUARD 450k past 440k:"), r.stderr


def test_05_a_missing_transcript_passes_silently(tmp_path):
    r = run(["--transcript", str(tmp_path / "nope.jsonl"), "--prompt", "continue"])
    assert_silent_pass(r, "missing transcript")


def test_06_a_sidechain_entry_at_the_end_does_not_count(tmp_path):
    t = write_transcript(tmp_path, [assistant(100000), assistant(900000, sidechain=True)])
    assert_silent_pass(run(["--transcript", str(t), "--prompt", "continue"]), "last main entry is 100k")


def test_07_the_threshold_option_overrides_the_default(tmp_path):
    t = write_transcript(tmp_path, [assistant(60000)])
    r = run(["--transcript", str(t), "--prompt", "continue", "--threshold", "1000"])
    assert r.returncode == 2, f"60k over a 1000 threshold must exit 2, got {r.returncode}"
    assert r.stderr.startswith("CONTEXT GUARD 60k past 1k:"), r.stderr


def test_08_a_six_megabyte_unparseable_tail_passes_fast_and_silent(tmp_path):
    t = tmp_path / "big.jsonl"
    t.write_text(json.dumps(assistant(450000)) + "\n" + "x" * (6 * 1024 * 1024))
    start = time.monotonic()
    r = run(["--transcript", str(t), "--prompt", "continue"])
    elapsed = time.monotonic() - start
    assert elapsed < 2.0, f"took {elapsed:.2f}s"
    assert_silent_pass(r, "tail window holds no parseable entry")
    # positive control: the same junk line followed by a 450k entry blocks, so the tail read does find entries
    t2 = tmp_path / "big2.jsonl"
    t2.write_text("x" * (6 * 1024 * 1024) + "\n" + json.dumps(assistant(450000)) + "\n")
    start = time.monotonic()
    r2 = run(["--transcript", str(t2), "--prompt", "continue"])
    assert time.monotonic() - start < 2.0, "the control run is also fast"
    assert r2.returncode == 2, f"junk then a 450k entry must exit 2, got {r2.returncode}"


def test_09_malformed_stdin_passes_silently(tmp_path):
    assert_silent_pass(run(stdin="this is not json {"), "malformed stdin")


def test_10_settings_wire_the_hook_and_the_compact_window():
    cfg = json.loads(SETTINGS.read_text())
    assert cfg.get("autoCompactWindow") == 400000, cfg.get("autoCompactWindow")
    entries = cfg.get("hooks", {}).get("UserPromptSubmit", [])
    cmds = [h.get("command", "") for e in entries for h in e.get("hooks", [])]
    assert any("context_guard.py" in c for c in cmds), cmds


def test_11_a_tool_call_past_the_threshold_is_blocked(tmp_path):
    t = write_transcript(tmp_path, [assistant(450000)])
    r = run(stdin=tool_json(t, "Bash", {"command": "ls"}))
    assert r.returncode == 2, f"Bash past 400k must exit 2, got {r.returncode}"
    assert r.stderr.startswith("CONTEXT GUARD 450k past 400k: tool call blocked;"), r.stderr
    assert r.stdout == "", r.stdout


def test_12_write_under_the_memory_dir_passes_and_outside_it_is_blocked(tmp_path):
    t = write_transcript(tmp_path, [assistant(450000)])
    mem = tmp_path / "mem"
    inside = mem / "proj" / "memory" / "continuation.md"
    outside = tmp_path / "other" / "notes.md"
    r = run(["--memory-dir", str(mem)], stdin=tool_json(t, "Write", {"file_path": str(inside), "content": "x"}))
    assert_silent_pass(r, "Write under the memory dir")
    r = run(["--memory-dir", str(mem)], stdin=tool_json(t, "Write", {"file_path": str(outside), "content": "x"}))
    assert r.returncode == 2, f"Write outside the memory dir must exit 2, got {r.returncode}"
    assert r.stderr.startswith("CONTEXT GUARD 450k past 400k: tool call blocked;"), r.stderr
