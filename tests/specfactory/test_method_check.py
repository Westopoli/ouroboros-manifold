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
RUNNER_IDS = {"wakeups", "polling", "gate_runs", "live_tree", "context"}
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
    return assistant(model, ctx=ctx, tools=[bash("git show origin/main:CLAUDE.md")])


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


def dispatcher_drift_entries(tmp_path, ctxs=(200000, 210000)):
    live = str(tmp_path / "live")
    return [
        assistant(SONNET, tools=[("ScheduleWakeup", {"delaySeconds": 270, "reason": "poll"})]),
        assistant(SONNET, tools=[bash("sleep 60 && ls")]),
        assistant(SONNET, tools=[bash("git commit -m wip")], cwd=live),
        assistant(SONNET, ctx=ctxs[0]),
        assistant(SONNET, ctx=ctxs[1]),
        compact(),
    ]


DRIFT_IDS = ["wakeups", "polling", "live_tree"]
OVER_400K = (410000, 420000)  # DEC-compaction-400k-2026-10-30: the context rule fires strictly past 400000


def test_script_exists():
    assert SCRIPT.exists(), f"missing {SCRIPT.relative_to(REPO)}"


def test_positive_control_clean_dispatcher(tmp_path):
    t = write_transcript(tmp_path, [clean_turn(), clean_turn()])
    r = run(tmp_path, t)
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    assert RUNNER_IDS <= set(got), f"missing checks {RUNNER_IDS - set(got)}"
    assert "code_edits" not in got  # architect-only
    for cid, (v, span, _sess) in got.items():
        assert v == "OK", f"{cid} is {v} on a clean transcript"
        assert span == 0, cid
    assert verdict(r.stdout) == "OK"
    m = HEADER_RE.match(next(l for l in r.stdout.splitlines() if l.startswith("METHOD role")))
    assert m and m.group(1) == "runner" and m.group(2) == SONNET and m.group(4) == "2"


def test_dispatcher_drift_before_compaction(tmp_path):
    entries = dispatcher_drift_entries(tmp_path, OVER_400K)
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    for cid in DRIFT_IDS:
        assert got[cid] == ("DRIFT", 1, 1), cid
    assert got["context"] == ("DRIFT", 2, 2)
    assert got["gate_runs"][0] == "OK"
    assert verdict(r.stdout) == "DRIFT"
    header = next(l for l in r.stdout.splitlines() if l.startswith("METHOD role"))
    m = HEADER_RE.match(header)
    assert m and m.group(1) == "runner" and m.group(4) == "5"
    assert m.group(5) == entries[0]["timestamp"]


def test_drift_span_resets_after_compaction_session_does_not(tmp_path):
    entries = dispatcher_drift_entries(tmp_path, OVER_400K) + [clean_turn()]
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
    r = run(tmp_path, write_transcript(tmp_path, dispatcher_drift_entries(tmp_path, OVER_400K)))
    lines = r.stdout.splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith("METHOD wakeups DRIFT"))
    assert lines[i + 1].startswith("  ") and "ScheduleWakeup" in lines[i + 1]
    j = next(n for n, l in enumerate(lines) if l.startswith("METHOD context DRIFT"))
    assert "context 420000" in lines[j + 1] and "context 410000" in lines[j + 2]


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
        assistant(FABLE, tools=[bash("bash scripts/specfactory/merge_gate.sh")]),
    ]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    for cid in ("code_edits", "gate_runs"):
        assert got[cid] == ("DRIFT", 1, 1), cid
    assert "METHOD role architect" in r.stdout
    assert verdict(r.stdout) == "DRIFT"


def test_unknown_role_shows_the_architect_rule(tmp_path):
    t = write_transcript(tmp_path, [assistant("claude-haiku-5-5", tools=[bash("ls")])])
    r = run(tmp_path, t)
    assert r.returncode == 0, r.stderr
    assert "METHOD role unknown" in r.stdout
    assert "claude-haiku-5-5" in next(l for l in r.stdout.splitlines() if l.startswith("METHOD role"))
    got = checks(r.stdout)
    assert got["code_edits"][0] == "OK"


def test_mixed_models_role_comes_from_the_last_model(tmp_path):
    # method_check.md "Role:": last assistant entry's model sets the role; header lists the others
    opus = "claude-opus-5-5"
    entries = [clean_turn(opus), clean_turn(opus), clean_turn(), clean_turn(), clean_turn()]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    header = next(l for l in r.stdout.splitlines() if l.startswith("METHOD role"))
    assert header.startswith(f"METHOD role runner model {SONNET} (session also {opus})"), header
    assert "code_edits" not in checks(r.stdout)  # architect-only rule, role is runner


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


def test_sidechain_turns_do_not_count(tmp_path):
    side = assistant(SONNET, tools=[("ScheduleWakeup", {"delaySeconds": 60})])
    side["isSidechain"] = True
    r = run(tmp_path, write_transcript(tmp_path, [clean_turn(), side]))
    assert checks(r.stdout)["wakeups"] == ("OK", 0, 0)


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


# ---- method rev 3, HARNESS-mm-4 (spec G20): the Architect's runner scripts under om-push/scratch are not code edits
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md G20 "In force"
def test_mm4_architect_write_under_scratch_is_not_a_code_edit(tmp_path):
    scratch = os.path.expanduser("~/Projects/om-push/scratch/runner.py")
    entries = [assistant(FABLE, tools=[("Write", {"file_path": scratch, "content": "x"})])]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    assert checks(r.stdout)["code_edits"][0] == "OK", r.stdout


def test_mm4_architect_write_under_scripts_is_still_a_code_edit(tmp_path):
    sc = os.path.expanduser("~/Projects/om-push/wt/x/scripts/runner.py")
    entries = [assistant(FABLE, tools=[("Write", {"file_path": sc, "content": "x"})])]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert checks(r.stdout)["code_edits"] == ("DRIFT", 1, 1), r.stdout


def test_mm4_scratch_shell_redirect_is_not_a_code_edit_either(tmp_path):
    cmd = "cat > ~/Projects/om-push/scratch/run_gate.sh <<'EOF'\necho hi\nEOF"
    r = run(tmp_path, write_transcript(tmp_path, [assistant(FABLE, tools=[bash(cmd)])]))
    assert checks(r.stdout)["code_edits"][0] == "OK", r.stdout


# ---- H-005 (docs/stories/H-005.md): the method check tests six rules and cites docs/method/, not retired documents
SIX_RULES = {"polling", "wakeups", "gate_runs", "live_tree", "code_edits", "context"}


def test_h005_six_rule_counts_on_the_existing_fixture(tmp_path):
    """H-005 Tests: "The existing fixture transcript yields the same six counts as today (positive control)."
    Story: "the rule table drops to six DRIFT checks (polling, wakeups, gate runs in a chat, live tree,
    code edits by Fable, context past 400k)"."""
    r = run(tmp_path, write_transcript(tmp_path, dispatcher_drift_entries(tmp_path)))
    assert r.returncode == 0, r.stderr
    got = checks(r.stdout)
    for cid in ("wakeups", "polling", "live_tree"):
        assert got[cid] == ("DRIFT", 1, 1), cid
    assert got["context"] == ("OK", 0, 0)  # fixture ctx is 200k/210k, under today's 400k default
    assert got["gate_runs"][0] == "OK"
    assert set(got) <= SIX_RULES, f"rules beyond the six: {sorted(set(got) - SIX_RULES)}"
    fable = run(tmp_path, write_transcript(tmp_path, [assistant(FABLE, tools=[
        ("Write", {"file_path": str(tmp_path / "x" / "foo.gd"), "content": "x"})])], name="f.jsonl"))
    fgot = checks(fable.stdout)
    assert fgot["code_edits"] == ("DRIFT", 1, 1)
    assert set(fgot) == SIX_RULES, f"rules beyond the six: {sorted(set(fgot) - SIX_RULES)}"


def test_h005_method_check_cites_no_retired_document():
    """H-005 Tests: "`grep -n 'dispatcher.md\\|context_architect\\|ledger row\\|lane table'
    scripts/specfactory/method_check.py` is empty." Story: every rule text cites `docs/method/<card>.md`."""
    pat = re.compile(r"dispatcher\.md|context_architect|ledger row|lane table")
    hits = [f"{n}: {l.strip()[:80]}" for n, l in enumerate(SCRIPT.read_text().splitlines(), 1) if pat.search(l)]
    assert not hits, "retired citations:\n" + "\n".join(hits)


def test_h005_hook_output_on_an_empty_transcript_lists_exactly_six_rules(tmp_path):
    """H-005 Tests: "The hook output on an empty transcript lists exactly six rules." """
    t = tmp_path / "empty.jsonl"
    t.write_text("")
    r = run(tmp_path, t)
    assert r.returncode == 0, r.stderr
    ids = [m.group(1) for m in map(LINE_RE.match, r.stdout.splitlines()) if m]
    assert len(ids) == 6 and set(ids) == SIX_RULES, f"{len(ids)} rules: {ids}"
