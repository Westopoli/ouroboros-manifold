# spec: docs/northstar/plans/workflows_2026-10-07/method_check.md "Test"; rules.md section (d)
"""Method check at compaction: scripts/specfactory/method_check.py over synthetic transcripts."""
import itertools
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "method_check.py"
WT = os.path.expanduser("~/Projects/om-push/wt/x")  # a worktree path; it need not exist
SONNET = "claude-sonnet-5-5"
FABLE = "claude-fable-5-1"
LINE_RE = re.compile(r"^METHOD (\w+) (OK|DRIFT|REVIEW) span (\d+) session (\d+)")
HEADER_RE = re.compile(r"^METHOD role (\w+) model (\S+) session (\S+) span \d+ of \d+ turns (\d+) since (\S+)")
DISPATCHER_IDS = {"wakeups", "polling", "gate_runs", "spawn_model", "fable_spawns", "live_tree",
                  "repo_edits", "main_push", "context", "messages", "live_reads", "workflows"}
_clock = itertools.count()


def _ts():
    n = next(_clock)
    return f"2026-10-10T10:{n // 60:02d}:{n % 60:02d}.000Z"


def assistant(model, tools=(), ctx=60000, ts=None, cwd=WT):
    """One assistant entry. tools: list of (name, input dict). ctx is split over the three usage fields."""
    content = [{"type": "tool_use", "id": f"t{i}", "name": n, "input": inp} for i, (n, inp) in enumerate(tools)]
    if not content:
        content = [{"type": "text", "text": "ok"}]
    return {"type": "assistant", "isSidechain": False, "cwd": cwd, "timestamp": ts or _ts(),
            "message": {"model": model,
                        "usage": {"input_tokens": 1000, "cache_read_input_tokens": ctx - 1500,
                                  "cache_creation_input_tokens": 500},
                        "content": content}}


def compact():
    return {"type": "user", "isCompactSummary": True, "message": {"role": "user", "content": "summary"}}


def bash(cmd):
    return ("Bash", {"command": cmd})


def clean_turn(model=SONNET, ctx=60000):
    return assistant(model, ctx=ctx, tools=[
        bash("git show origin/main:CLAUDE.md"),
        ("Agent", {"subagent_type": "engineer", "model": "sonnet", "prompt": "x"}),
        ("Workflow", {"scriptPath": "x.js"})])


def write_transcript(tmp_path, entries, name="t.jsonl", extra_lines=()):
    p = tmp_path / name
    lines = [json.dumps(e) for e in entries] + list(extra_lines)
    p.write_text("\n".join(lines) + "\n")
    return p


def run(tmp_path, transcript, *extra, stdin=None):
    live = tmp_path / "live"
    live.mkdir(exist_ok=True)
    args = [sys.executable, str(SCRIPT), "--live-checkout", str(live)]
    if transcript is not None:
        args += ["--transcript", str(transcript)]
    args += list(extra)
    return subprocess.run(args, input=stdin, capture_output=True, text=True, timeout=60)


def checks(out):
    """Map check id -> (verdict, span, session) from the METHOD check lines."""
    found = {}
    for line in out.splitlines():
        m = LINE_RE.match(line)
        if m:
            found[m.group(1)] = (m.group(2), int(m.group(3)), int(m.group(4)))
    return found


def verdict(out):
    m = re.search(r"^METHOD verdict (OK|DRIFT)\s*$", out, re.M)
    assert m, f"no METHOD verdict line in:\n{out}"
    return m.group(1)


def rules_block(out, role):
    """Lines after `METHOD rules <role>` up to the next METHOD line."""
    lines = out.splitlines()
    start = lines.index(f"METHOD rules {role}")
    block = []
    for line in lines[start + 1:]:
        if line.startswith("METHOD"):
            break
        block.append(line)
    return "\n".join(block)


def dispatcher_drift_entries(tmp_path):
    live = str(tmp_path / "live")
    return [
        assistant(SONNET, tools=[("ScheduleWakeup", {"delaySeconds": 270, "reason": "poll"})]),
        assistant(SONNET, tools=[bash("sleep 60 && ls")]),
        assistant(SONNET, tools=[("Agent", {"subagent_type": "engineer", "prompt": "x"})]),
        assistant(SONNET, tools=[("Agent", {"subagent_type": "engineer", "model": "fable", "prompt": "x"})]),
        assistant(SONNET, tools=[bash("git commit -m wip")], cwd=live),
        assistant(SONNET, tools=[bash("git push origin main")]),
        assistant(SONNET, ctx=200000),
        assistant(SONNET, ctx=210000),
        compact(),
    ]


DRIFT_IDS = ["wakeups", "polling", "spawn_model", "fable_spawns", "live_tree", "main_push"]


def test_script_exists():
    assert SCRIPT.exists(), f"missing {SCRIPT.relative_to(REPO)}"


def test_positive_control_clean_dispatcher(tmp_path):
    t = write_transcript(tmp_path, [clean_turn(), clean_turn()])
    r = run(tmp_path, t)
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    assert DISPATCHER_IDS <= set(got), f"missing checks {DISPATCHER_IDS - set(got)}"
    assert "code_edits" not in got  # architect-only
    for cid, (v, span, _sess) in got.items():
        assert v in ("OK", "REVIEW"), f"{cid} is {v} on a clean transcript"
        if v == "OK":
            assert span == 0, cid
    for cid in ("messages", "live_reads", "workflows"):
        assert got[cid][0] == "REVIEW", cid
    assert got["workflows"][1:] == (2, 2)
    assert verdict(r.stdout) == "OK"
    m = HEADER_RE.match(next(l for l in r.stdout.splitlines() if l.startswith("METHOD role")))
    assert m and m.group(1) == "dispatcher" and m.group(2) == SONNET and m.group(4) == "2"


def test_dispatcher_drift_before_compaction(tmp_path):
    entries = dispatcher_drift_entries(tmp_path)
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    for cid in DRIFT_IDS:
        assert got[cid] == ("DRIFT", 1, 1), cid
    assert got["context"] == ("DRIFT", 2, 2)
    for cid in ("gate_runs", "repo_edits"):
        assert got[cid][0] == "OK", cid
    assert verdict(r.stdout) == "DRIFT"
    header = next(l for l in r.stdout.splitlines() if l.startswith("METHOD role"))
    m = HEADER_RE.match(header)
    assert m and m.group(1) == "dispatcher" and m.group(4) == "8"
    assert m.group(5) == entries[0]["timestamp"]


def test_drift_span_resets_after_compaction_session_does_not(tmp_path):
    entries = dispatcher_drift_entries(tmp_path) + [clean_turn()]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    for cid in DRIFT_IDS:
        assert got[cid] == ("OK", 0, 1), cid
    assert got["context"] == ("OK", 0, 2)
    assert verdict(r.stdout) == "OK"
    header = next(l for l in r.stdout.splitlines() if l.startswith("METHOD role"))
    assert HEADER_RE.match(header).group(4) == "1"


def test_excerpts_name_the_decisive_lines(tmp_path):
    r = run(tmp_path, write_transcript(tmp_path, dispatcher_drift_entries(tmp_path)))
    lines = r.stdout.splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith("METHOD wakeups DRIFT"))
    assert lines[i + 1].startswith("  ") and "ScheduleWakeup" in lines[i + 1]
    j = next(n for n, l in enumerate(lines) if l.startswith("METHOD context DRIFT"))
    assert "context 210000" in lines[j + 1] and "context 200000" in lines[j + 2]


def test_excerpt_from_session_when_span_is_clean(tmp_path):
    entries = dispatcher_drift_entries(tmp_path) + [clean_turn()]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    lines = r.stdout.splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith("METHOD wakeups OK"))
    assert "ScheduleWakeup" in lines[i + 1]


def test_architect_checks(tmp_path):
    gd = str(tmp_path / "elsewhere" / "foo.gd")
    entries = [
        assistant(FABLE, tools=[("Write", {"file_path": gd, "content": "x"})]),
        assistant(FABLE, tools=[("Agent", {"subagent_type": "architect", "model": "sonnet", "prompt": "x"})]),
        assistant(FABLE, tools=[bash("bash scripts/specfactory/merge_gate.sh")]),
    ]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    for cid in ("code_edits", "fable_spawns", "gate_runs"):
        assert got[cid] == ("DRIFT", 1, 1), cid
    assert "METHOD repo_edits" not in r.stdout
    assert "METHOD main_push" not in r.stdout
    assert "METHOD role architect" in r.stdout
    assert verdict(r.stdout) == "DRIFT"


def test_dispatcher_may_spawn_architect(tmp_path):
    t = write_transcript(tmp_path, [assistant(SONNET, tools=[
        ("Agent", {"subagent_type": "architect", "model": "fable", "prompt": "x"})])])
    got = checks(run(tmp_path, t).stdout)
    assert got["fable_spawns"][0] == "OK"


def test_unknown_role_prints_both_rule_lists(tmp_path):
    t = write_transcript(tmp_path, [assistant("claude-haiku-5-5", tools=[bash("ls")])])
    r = run(tmp_path, t)
    assert r.returncode == 0, r.stderr
    assert "METHOD role unknown" in r.stdout
    assert "claude-haiku-5-5" in next(l for l in r.stdout.splitlines() if l.startswith("METHOD role"))
    got = checks(r.stdout)
    for cid in ("code_edits", "repo_edits", "main_push"):
        assert got[cid][0] == "REVIEW", cid
    unknown = rules_block(r.stdout, "unknown")
    assert "names its model" in unknown and "lane table" in unknown and "writes no code" in unknown


def test_mixed_models_role_comes_from_the_last_model(tmp_path):
    # method_check.md "Role:": last assistant entry's model sets the role; header lists the others
    opus = "claude-opus-5-5"
    entries = [clean_turn(opus), clean_turn(opus), clean_turn(), clean_turn(), clean_turn()]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    header = next(l for l in r.stdout.splitlines() if l.startswith("METHOD role"))
    assert header.startswith(f"METHOD role dispatcher model {SONNET} (session also {opus})"), header
    got = checks(r.stdout)
    assert got["repo_edits"][0] == "OK", got["repo_edits"]
    assert got["main_push"][0] == "OK", got["main_push"]
    assert "METHOD rules dispatcher" in r.stdout.splitlines()
    assert "METHOD rules architect" not in r.stdout.splitlines()


def test_threshold_option(tmp_path):
    t = write_transcript(tmp_path, [assistant(SONNET, ctx=5000)])
    assert checks(run(tmp_path, t).stdout)["context"] == ("OK", 0, 0)
    r = run(tmp_path, t, "--threshold", "1000")
    assert checks(r.stdout)["context"] == ("DRIFT", 1, 1)
    assert verdict(r.stdout) == "DRIFT"
    r10 = run(tmp_path, t, "--threshold", "10")
    assert checks(r10.stdout)["context"][0] == "DRIFT"


def test_stdin_json_input(tmp_path):
    t = write_transcript(tmp_path, [clean_turn()])
    payload = json.dumps({"transcript_path": str(t), "session_id": "abcdef1234567890", "source": "compact"})
    r = run(tmp_path, None, stdin=payload)
    assert r.returncode == 0, r.stderr
    header = next(l for l in r.stdout.splitlines() if l.startswith("METHOD role"))
    assert "session abcdef12 " in header and "abcdef123" not in header
    assert verdict(r.stdout) == "OK"


def test_missing_path_is_an_error_line_and_exit_zero(tmp_path):
    r = run(tmp_path, tmp_path / "no_such.jsonl")
    assert r.returncode == 0
    assert r.stdout.startswith("METHOD error"), r.stdout
    r2 = run(tmp_path, None, stdin=json.dumps({"transcript_path": str(tmp_path / "gone.jsonl"),
                                               "session_id": "abcdef1234", "source": "compact"}))
    assert r2.returncode == 0 and r2.stdout.startswith("METHOD error"), r2.stdout


def test_non_json_line_is_skipped(tmp_path):
    t = write_transcript(tmp_path, [clean_turn(), clean_turn()], extra_lines=["this is not json {"])
    r = run(tmp_path, t)
    assert r.returncode == 0, r.stderr
    assert "METHOD error" not in r.stdout
    assert verdict(r.stdout) == "OK"
    assert checks(r.stdout)["workflows"][2] == 2


def test_sidechain_turns_do_not_count(tmp_path):
    side = assistant(SONNET, tools=[("ScheduleWakeup", {"delaySeconds": 60})])
    side["isSidechain"] = True
    r = run(tmp_path, write_transcript(tmp_path, [clean_turn(), side]))
    assert checks(r.stdout)["wakeups"] == ("OK", 0, 0)


def test_rule_lists(tmp_path):
    d = run(tmp_path, write_transcript(tmp_path, [clean_turn()], name="d.jsonl"))
    block = rules_block(d.stdout, "dispatcher")
    assert "names its model" in block and "lane table" in block
    assert "writes no code" not in block
    a = run(tmp_path, write_transcript(tmp_path, [assistant(FABLE, tools=[bash("ls")])], name="a.jsonl"))
    ablock = rules_block(a.stdout, "architect")
    assert "writes no code" in ablock
    assert "lane table" not in ablock


def test_next_line_is_last(tmp_path):
    for entries in ([clean_turn()], dispatcher_drift_entries(tmp_path)):
        r = run(tmp_path, write_transcript(tmp_path, entries))
        out = [l for l in r.stdout.splitlines() if l.strip()]
        assert out[-1].startswith("METHOD next:"), out[-1]
        assert "Westley" in out[-1]
        assert all(l.startswith("METHOD") or l.startswith("  ") or l.startswith("- ") for l in out), out


def test_bash_words_in_heredoc_or_reader_segments_count_for_nothing(tmp_path):
    # method_check.md: Bash text is matched after heredoc bodies are removed and per segment
    entries = [
        assistant(SONNET, tools=[bash("cat > x.md <<'EOF'\nsleep and merge_gate.sh are words\nEOF")]),
        assistant(SONNET, tools=[bash("grep merge_gate.sh scripts/x")]),
        assistant(SONNET, tools=[bash("git show origin/main:scripts/specfactory/merge_gate.sh")]),
    ]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    assert got["polling"][:2] == ("OK", 0), got["polling"]
    assert got["gate_runs"][:2] == ("OK", 0), got["gate_runs"]


def test_bash_sleep_flock_and_gate_script_segments_count(tmp_path):
    entries = [
        assistant(SONNET, tools=[bash("sleep 120")]),
        assistant(SONNET, tools=[bash("flock ~/Projects/om-push/gate.lock x")]),
        assistant(SONNET, tools=[bash("cd /w && bash scripts/specfactory/merge_gate.sh wt main P")]),
    ]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    assert got["polling"][:2] == ("DRIFT", 2), got["polling"]
    assert got["gate_runs"][:2] == ("DRIFT", 1), got["gate_runs"]
