"""HARNESS-cost-report: tests for scripts/specfactory/cost_report.py, the usage-metadata cost script.
(No bible rule states the tool, so there is no R-/S- id to pin and no `Rule pins:` line is needed: the id proved
by every case is the piece id HARNESS-cost-report.)

Authority: docs/northstar/plans/2026-10-21-tool-split-spec.md section 6, bullet "HARNESS-cost-report" (first
sentence: "`scripts/specfactory/cost_report.py`, the usage-metadata cost script (from the Architect's scratch
`cost/cost.py`; reads only `timestamp`, `type`, `sessionId`, `message.model`, `message.usage`, `requestId` and the file
path, never content; DEDUP by `requestId` ..."). The bullet's own dedup and field text is superseded by the INTERFACE
and the Architect rulings G1/G2 of 2026-10-21 in docs/northstar/plans/workflows_2026-10-07/vg-wave15-harness-costreport.js
(IFACE items 1 to 9, ARCH_RULINGS); each case below says which item it proves. Rates are DRAFT-cost-rates (USD per
million tokens: input, output, cache_write, cache_read): Opus/Fable 15, 75, 18.75, 1.5; Sonnet 3, 15, 3.75, 0.30;
Haiku 0.8, 4, 1, 0.08.

UNSTATED INTERFACE choices made here (none is a rule; a builder follows the INTERFACE, the Architect may veto):
  U1 the default of --by is not stated anywhere, so every run here passes --by explicitly.
  U2 table parsing: header row of the seven column names, whitespace separated; est_usd is compared as a float
     within 1e-6 (the 6-decimal print format is asserted separately by regex), because a half-way digit such as
     0.0134325 has no fixed rounding.
  U3 the unpermitted-field marker test plants the marker in message.content and in a top-level field "cwd".
  U4 stderr of a successful table-mode run is not asserted empty (only the content test reads it).

Fixture (written by the tests into tmp_path as <root>/..., three files, ten counting lines, two models, two days).
Files sort as strings of the relative path: "s1.jsonl" < "s1/subagents/agent-a.jsonl" < "s1/subagents/workflows/agent-w.jsonl".
 file A s1.jsonl (role main, sessionId s1):
   L1 req r1 day 20 sonnet (in,out,cw,cr)=(100, 10,   0,    0)  DROPPED by requestId (earlier line of the group)
   L2 req r1 day 20 sonnet (100, 50,  200,  1000) kept (last of r1)
   L3 req r2 day 20 opus   (10,  20,  30,   40)
   L4 no req day 21 sonnet (5,   6,   7,    8)                 kept (first of its tuple in this file)
   L5 no req day 21 sonnet (5,   6,   7,    8)                 DROPPED by tuple (same file as L4)
 file B s1/subagents/agent-a.jsonl (role subagent, sessionId s1):
   L6 req r3 day 21 opus   (1000, 2000, 3000, 4000)
   L7 no req day 21 sonnet (5,   6,   7,    8)                 kept (same tuple as L4 but another file)
   L8 req r4 day 20 sonnet (1,   2,   3,    4)
 file C s1/subagents/workflows/agent-w.jsonl (role workflow-agent, sessionId s2):
   L9 req r5 day 21 opus   (50,  60,  70,   80)
   L10 req r6 day 21 sonnet (200, 300, 400,  500)
 Kept: 8 turns. "dedup: 1 by requestId, 1 by tuple".
By hand, dollars = sum(tokens x rate) / 1e6:
   L2  = (100x3 + 50x15 + 200x3.75 + 1000x0.30)/1e6 = (300+750+750+300)/1e6 = 0.002100
   L3  = (10x15 + 20x75 + 30x18.75 + 40x1.5)/1e6 = (150+1500+562.5+60)/1e6 = 0.0022725
   L4 = L7 = (15+90+26.25+2.4)/1e6 = 0.00013365 ; L8 = (3+30+11.25+1.2)/1e6 = 0.00004545
   L6  = (15000+150000+56250+6000)/1e6 = 0.22725 ; L9 = (750+4500+1312.5+120)/1e6 = 0.0066825
   L10 = (600+4500+1500+150)/1e6 = 0.00675
 Totals (turns; in, out, cw, cr; usd): ALL 8; 1371, 2444, 3717, 5640; 0.24536775
   day 2026-10-20: 3; 111, 72, 233, 1044; 0.00441795    day 2026-10-21: 5; 1260, 2372, 3484, 4596; 0.2409498
   session s1: 6; 1121, 2084, 3247, 5060; 0.2319353      session s2: 2; 250, 360, 470, 580; 0.0134325
   role main: 3; 115, 76, 237, 1048; 0.00450615   subagent: 3; 1006, 2008, 3010, 4012; 0.2274291
   role workflow-agent: 2; 250, 360, 470, 580; 0.0134325
 Note line: output total is m = 50+20+6+2000+6+2+60+300 = 2444 (keep-last); keep-first on group r1 gives 10 not 50,
   so n = 2444 - 40 = 2404: "note: keep-first would give 2404 output tokens, keep-last 2444".
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "specfactory" / "cost_report.py"
COLUMNS = ["key", "turns", "input", "output", "cache_write", "cache_read", "est_usd"]
SONNET, OPUS = "claude-sonnet-5-5", "claude-opus-5-5"


def _line(day, model, usage, req=None, sid="s1", typ="assistant", hour="10", **extra):
    keys = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
    d = {"type": typ, "sessionId": sid, "timestamp": f"2026-10-{day}T{hour}:00:00.000Z",
         "message": {"model": model, "usage": dict(zip(keys, usage)), "content": "x"}}
    if req:
        d["requestId"] = req
    d.update(extra)
    return d


def _write(root: Path, rel: str, lines):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join((l if isinstance(l, str) else json.dumps(l)) + "\n" for l in lines))


FILE_A = "s1.jsonl"
FILE_B = "s1/subagents/agent-a.jsonl"
FILE_C = "s1/subagents/workflows/agent-w.jsonl"


def _main_fixture(root: Path):
    _write(root, FILE_A, [
        _line("20", SONNET, (100, 10, 0, 0), "r1"),
        _line("20", SONNET, (100, 50, 200, 1000), "r1"),
        _line("20", OPUS, (10, 20, 30, 40), "r2"),
        _line("21", SONNET, (5, 6, 7, 8)),
        _line("21", SONNET, (5, 6, 7, 8)),
    ])
    _write(root, FILE_B, [
        _line("21", OPUS, (1000, 2000, 3000, 4000), "r3"),
        _line("21", SONNET, (5, 6, 7, 8)),
        _line("20", SONNET, (1, 2, 3, 4), "r4"),
    ])
    _write(root, FILE_C, [
        _line("21", OPUS, (50, 60, 70, 80), "r5", sid="s2"),
        _line("21", SONNET, (200, 300, 400, 500), "r6", sid="s2"),
    ])


def _run(*args, home=None):
    assert SCRIPT.is_file(), f"scripts/specfactory/cost_report.py is missing: {SCRIPT}"
    env = None
    if home is not None:
        import os
        env = dict(os.environ, HOME=str(home))
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          timeout=60, cwd=REPO_ROOT, env=env)


def _table(stdout: str):
    """{key: [turns, input, output, cache_write, cache_read, est_usd]} from the table; checks the header."""
    lines = [l for l in stdout.splitlines() if l.strip()]
    assert lines and lines[0].split() == COLUMNS, f"header row is not {COLUMNS}: {lines[:1]}"
    rows = {}
    for l in lines[1:]:
        f = l.split()
        if len(f) == 7 and re.fullmatch(r"-?\d+\.\d{6}", f[6]):
            rows[f[0]] = [int(x) for x in f[1:6]] + [float(f[6])]
    return rows, lines


def _check(row, turns, tokens, usd):
    assert row[:5] == [turns, *tokens], f"row {row}"
    assert abs(row[5] - usd) <= 1e-6, f"usd {row[5]} vs {usd}"


TOTAL = (8, (1371, 2444, 3717, 5640), 0.24536775)
DEDUP_LINE = "dedup: 1 by requestId, 1 by tuple"
NOTE_LINE = "note: keep-first would give 2404 output tokens, keep-last 2444"


# ------------------------------------------------------- positive controls --

def test_control_fixture_would_fail_without_dedup(tmp_path):
    """Control (HARNESS-cost-report, IFACE 7): the raw sums of the ten lines are NOT the expected totals, so a tool
    that skips dedup or keeps the wrong line cannot pass the totals test. Runs without product code."""
    _main_fixture(tmp_path)
    raw_out = 0
    for rel in (FILE_A, FILE_B, FILE_C):
        for l in (tmp_path / rel).read_text().splitlines():
            raw_out += json.loads(l)["message"]["usage"]["output_tokens"]
    assert raw_out == 2444 + 10 + 6  # kept 2444, plus L1's 10 and L5's 6
    assert raw_out != TOTAL[1][1]
    assert 2404 != 2444  # the note's n differs from m, so keep-first vs keep-last is observable


def test_control_table_parser_rejects_a_wrong_header():
    """Control (HARNESS-cost-report, IFACE 6): the helper's header check is live."""
    try:
        _table("key turns\nTOTAL 0\n")
    except AssertionError:
        return
    raise AssertionError("_table accepted a wrong header")


# ----------------------------------------------------------------- totals --

def test_totals_by_session_with_dedup_and_note(tmp_path):
    """HARNESS-cost-report IFACE 3, 5, 6, 7: ten lines, two dropped; totals, dollars, dedup and note lines."""
    _main_fixture(tmp_path)
    r = _run("--root", str(tmp_path), "--by", "session")
    assert r.returncode == 0, r.stderr
    rows, lines = _table(r.stdout)
    _check(rows["s1"], 6, (1121, 2084, 3247, 5060), 0.2319353)
    _check(rows["s2"], 2, (250, 360, 470, 580), 0.0134325)
    _check(rows["TOTAL"], *TOTAL)
    assert list(rows) == ["s1", "s2", "TOTAL"]  # key ascending, TOTAL last
    out = r.stdout.splitlines()
    assert out.index(DEDUP_LINE) < out.index(NOTE_LINE)
    assert out.index(DEDUP_LINE) > max(i for i, l in enumerate(out) if l.startswith("TOTAL"))
    assert not any(l.startswith("no rate:") for l in out)  # both models are priced


def test_by_day_uses_first_ten_characters_of_timestamp(tmp_path):
    """HARNESS-cost-report G2 (1) and (4): --by day, key is the date of the timestamp."""
    _main_fixture(tmp_path)
    r = _run("--root", str(tmp_path), "--by", "day")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    _check(rows["2026-10-20"], 3, (111, 72, 233, 1044), 0.00441795)
    _check(rows["2026-10-21"], 5, (1260, 2372, 3484, 4596), 0.2409498)
    _check(rows["TOTAL"], *TOTAL)
    assert list(rows) == ["2026-10-20", "2026-10-21", "TOTAL"]


def test_by_role_derived_from_path_below_root(tmp_path):
    """HARNESS-cost-report G1: main / subagent / workflow-agent from the path relative to --root."""
    _main_fixture(tmp_path)
    r = _run("--root", str(tmp_path), "--by", "role")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    _check(rows["main"], 3, (115, 76, 237, 1048), 0.00450615)
    _check(rows["subagent"], 3, (1006, 2008, 3010, 4012), 0.2274291)
    _check(rows["workflow-agent"], 2, (250, 360, 470, 580), 0.0134325)
    _check(rows["TOTAL"], *TOTAL)
    assert list(rows) == ["main", "subagent", "workflow-agent", "TOTAL"]


def test_directory_named_subagents_above_root_changes_nothing(tmp_path):
    """HARNESS-cost-report G1 last sentence: only the path below --root decides the role."""
    root = tmp_path / "subagents" / "proj"
    _write(root, "s9.jsonl", [_line("20", SONNET, (1, 2, 3, 4), "q1", sid="s9")])
    r = _run("--root", str(root), "--by", "role")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    assert list(rows) == ["main", "TOTAL"]


def test_est_usd_has_six_decimals(tmp_path):
    """HARNESS-cost-report G2 (4): est_usd printed with 6 decimals."""
    _main_fixture(tmp_path)
    r = _run("--root", str(tmp_path), "--by", "session")
    total = [l for l in r.stdout.splitlines() if l.startswith("TOTAL")][0].split()
    assert re.fullmatch(r"\d+\.\d{6}", total[6]), total


# ------------------------------------------------------------ since/until --

def test_since_filters_by_day_but_dedup_counts_cover_the_run(tmp_path):
    """HARNESS-cost-report IFACE 3 (dedup before the filter) and G2 (1): --since 2026-10-21."""
    _main_fixture(tmp_path)
    r = _run("--root", str(tmp_path), "--by", "day", "--since", "2026-10-21")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    assert list(rows) == ["2026-10-21", "TOTAL"]
    _check(rows["TOTAL"], 5, (1260, 2372, 3484, 4596), 0.2409498)
    out = r.stdout.splitlines()
    assert DEDUP_LINE in out  # L1 (day 20) is outside the filter but still counted as dropped
    assert "note: keep-first would give 2372 output tokens, keep-last 2372" in out


def test_until_includes_its_whole_day(tmp_path):
    """HARNESS-cost-report G2 (1): --until 2026-10-20 keeps every line of that day, late hours included."""
    _main_fixture(tmp_path)
    _write(tmp_path, "late.jsonl", [_line("20", SONNET, (1, 1, 1, 1), "z1", hour="23", sid="s3")])
    r = _run("--root", str(tmp_path), "--by", "day", "--until", "2026-10-20")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    assert list(rows) == ["2026-10-20", "TOTAL"]
    _check(rows["TOTAL"], 4, (112, 73, 234, 1045), 0.00441795 + (3 + 15 + 3.75 + 0.3) / 1e6)
    out = r.stdout.splitlines()
    assert "note: keep-first would give 33 output tokens, keep-last 73" in out  # r1 first line 10 instead of 50


# ------------------------------------------------------------------ dedup --

def test_requestid_group_keeps_last_line_across_files_in_string_sorted_order(tmp_path):
    """HARNESS-cost-report IFACE 3: one requestId in s1.jsonl and in s1/subagents/...; plain-string order puts
    s1.jsonl first, so the subagent file's line (out 99) is the last and is kept (a path-component sort would keep 10)."""
    _write(tmp_path, "s1.jsonl", [_line("20", SONNET, (1, 10, 0, 0), "g1")])
    _write(tmp_path, "s1/subagents/agent-a.jsonl", [_line("20", SONNET, (1, 99, 0, 0), "g1")])
    r = _run("--root", str(tmp_path), "--by", "role")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    assert list(rows) == ["subagent", "TOTAL"]
    assert rows["TOTAL"][:3] == [1, 1, 99]
    assert "dedup: 1 by requestId, 0 by tuple" in r.stdout.splitlines()


def test_tuple_fallback_is_per_file_and_keeps_first(tmp_path):
    """HARNESS-cost-report IFACE 3: same four numbers twice in one file count once; in two files, twice."""
    _write(tmp_path, "a.jsonl", [_line("20", SONNET, (4, 3, 2, 1)), _line("20", SONNET, (4, 3, 2, 1))])
    _write(tmp_path, "b.jsonl", [_line("20", SONNET, (4, 3, 2, 1))])
    r = _run("--root", str(tmp_path), "--by", "day")
    rows, _ = _table(r.stdout)
    assert rows["TOTAL"][:5] == [2, 8, 6, 4, 2]
    assert "dedup: 0 by requestId, 1 by tuple" in r.stdout.splitlines()


# -------------------------------------------------------------- rate rows --

def test_haiku_fable_rows_and_case_insensitive_match(tmp_path):
    """HARNESS-cost-report G2 (3) and IFACE 5: haiku 0.8+4+1+0.08, fable = Opus row 15+75+18.75+1.5, per 1e6 tokens each."""
    m = 1_000_000
    _write(tmp_path, "h.jsonl", [_line("20", "Claude-HAIKU-5-5", (m, m, m, m), "h1", sid="h")])
    _write(tmp_path, "f.jsonl", [_line("20", "claude-fable-5-1", (m, m, m, m), "f1", sid="f")])
    r = _run("--root", str(tmp_path), "--by", "session")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    assert abs(rows["h"][5] - 5.88) <= 1e-6
    assert abs(rows["f"][5] - 110.25) <= 1e-6


def test_unpriced_models_are_counted_priced_zero_and_listed_ascending(tmp_path):
    """HARNESS-cost-report G2 (3) and IFACE 9: "<synthetic>" and a missing model: tokens counted, usd 0, 'no rate:' lines."""
    _write(tmp_path, "a.jsonl", [
        _line("20", "<synthetic>", (1, 2, 3, 4), "u1"),
        _line("20", "zeta-model", (10, 20, 30, 40), "u2"),
        _line("20", "alpha-model", (100, 200, 300, 400), "u3"),
    ])
    nomodel = _line("20", SONNET, (7, 7, 7, 7), "u4")
    del nomodel["message"]["model"]
    _write(tmp_path, "b.jsonl", [nomodel])
    r = _run("--root", str(tmp_path), "--by", "day")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    _check(rows["TOTAL"], 4, (118, 229, 340, 451), 0.0)
    nr = [l for l in r.stdout.splitlines() if l.startswith("no rate:")]
    assert sorted(nr) == nr  # ascending
    assert set(nr) == {"no rate: <missing>", "no rate: <synthetic>", "no rate: alpha-model", "no rate: zeta-model"}


def test_rate_table_is_a_named_draft_in_the_source():
    """HARNESS-cost-report IFACE 5: one constant DRAFT_COST_RATES with the comment DRAFT-cost-rates, in the source."""
    assert SCRIPT.is_file(), f"scripts/specfactory/cost_report.py is missing: {SCRIPT}"
    src = SCRIPT.read_text()
    assert "DRAFT_COST_RATES" in src and "DRAFT-cost-rates" in src


# ------------------------------------------------------------------ edges --

def test_edges_skipped_lines_and_missing_usage_keys(tmp_path):
    """HARNESS-cost-report G2 (2) and IFACE 9: non-assistant, no usage, bad JSON, non-object, no timestamp are skipped;
    a missing usage key counts 0."""
    nots = _line("20", SONNET, (9, 9, 9, 9), "e5")
    del nots["timestamp"]
    nousage = _line("20", SONNET, (9, 9, 9, 9), "e3")
    del nousage["message"]["usage"]
    part = _line("20", SONNET, (4, 5, 6, 7), "e6")
    del part["message"]["usage"]["cache_read_input_tokens"]
    del part["message"]["usage"]["output_tokens"]
    _write(tmp_path, "a.jsonl", [
        _line("20", SONNET, (9, 9, 9, 9), "e1", typ="user"),
        "this is not json {",
        "[1, 2, 3]",
        '"a string"',
        nousage, nots, part,
    ])
    r = _run("--root", str(tmp_path), "--by", "day")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    assert rows["TOTAL"][:5] == [1, 4, 0, 6, 0]
    assert "dedup: 0 by requestId, 0 by tuple" in r.stdout.splitlines()


def test_empty_result_prints_header_and_zero_total(tmp_path):
    """HARNESS-cost-report IFACE 9: no line kept gives the header and a TOTAL row of zeros, exit 0."""
    _write(tmp_path, "a.jsonl", ["not json"])
    r = _run("--root", str(tmp_path), "--by", "day")
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    assert list(rows) == ["TOTAL"]
    _check(rows["TOTAL"], 0, (0, 0, 0, 0), 0.0)


def test_nonexistent_root_exits_2_with_stderr_only(tmp_path):
    """HARNESS-cost-report IFACE 9: a nonexistent --root exits 2, a message on stderr, nothing on stdout."""
    r = _run("--root", str(tmp_path / "nope"), "--by", "day")
    assert r.returncode == 2
    assert r.stdout == "" and r.stderr.strip()


def test_tilde_in_root_is_expanded(tmp_path):
    """HARNESS-cost-report IFACE 2: a ~ in --root is expanded (HOME points at tmp_path)."""
    _write(tmp_path, "proj/s1.jsonl", [_line("20", SONNET, (1, 2, 3, 4), "t1")])
    r = _run("--root", "~/proj", "--by", "day", home=tmp_path)
    assert r.returncode == 0, r.stderr
    rows, _ = _table(r.stdout)
    assert rows["TOTAL"][:5] == [1, 1, 2, 3, 4]


# -------------------------------------------------------------------- csv --

def test_csv_stdout_is_clean_and_extra_lines_go_to_stderr(tmp_path):
    """HARNESS-cost-report IFACE 6: with --csv stdout is header, rows, TOTAL only; dedup and note lines go to stderr."""
    _main_fixture(tmp_path)
    r = _run("--root", str(tmp_path), "--by", "session", "--csv")
    assert r.returncode == 0, r.stderr
    out = r.stdout.splitlines()
    assert out[0].split(",") == COLUMNS
    assert [l.split(",")[0] for l in out[1:]] == ["s1", "s2", "TOTAL"]
    assert out[3].split(",")[1:6] == ["8", "1371", "2444", "3717", "5640"]
    assert DEDUP_LINE not in r.stdout and "note:" not in r.stdout
    err = r.stderr.splitlines()
    assert DEDUP_LINE in err and NOTE_LINE in err


# ------------------------------------------------------------- no content --

def test_no_content_or_unpermitted_field_is_printed(tmp_path):
    """HARNESS-cost-report IFACE 8: a marker in message.content and one in top-level cwd never reach stdout or stderr."""
    _main_fixture(tmp_path)
    marker_c, marker_f = "MARKER-CONTENT-7f3a", "MARKER-FIELD-91bc"
    l = _line("20", SONNET, (1, 1, 1, 1), "m1", sid="s1", cwd=marker_f)
    l["message"]["content"] = [{"type": "text", "text": marker_c}]
    _write(tmp_path, "m.jsonl", [l])
    for extra in ([], ["--csv"]):
        r = _run("--root", str(tmp_path), "--by", "session", *extra)
        assert r.returncode == 0, r.stderr
        if not extra:
            rows, _ = _table(r.stdout)
            _check(rows["TOTAL"], 9, (1372, 2445, 3718, 5641), 0.24536775 + (3 + 15 + 3.75 + 0.3) / 1e6)
        assert marker_c not in r.stdout + r.stderr and marker_f not in r.stdout + r.stderr
