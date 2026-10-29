# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md Amendment A10 (items below) and A14; DEC-daily-allotment-2026-10-27,
# DEC-coordinator-wakeups-2026-10-27 (HARNESS-mm-12)
"""scripts/specfactory/token_ledger.py and the metrics M25 to M29 in method_metrics_runs.py, the `[estimates]` table in
method_thresholds.toml, the M06/M07 repair (top-level sessions priced by model) and METHOD_PATHS. Each case names its A10
item. Red on origin/main because the script is missing, the metric is missing, or the toml field is absent.
Case 11 of the brief (approvals) is HARNESS-mm-16's; here only the new tables' DRAFT state (`approved = ""`) is checked.
The fixture interfaces are listed in fixtures/token_ledger/tl_world.py."""
import csv
import re
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SPEC = REPO / "scripts" / "specfactory"
LEDGER = SPEC / "token_ledger.py"
METRICS = SPEC / "method_metrics.py"
TOML = SPEC / "method_thresholds.toml"
sys.path.insert(0, str(HERE / "fixtures" / "token_ledger"))
import tl_world as T  # noqa: E402

W = T.W
LINE = re.compile(r"^METRIC (\S+) (PASS|FAIL|DRAFT|NA) (.*)$")
NUM = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")


def nums(line):
    return [float(x.replace(",", "")) for x in NUM.findall(line)]


def has(line, want):
    return any(abs(n - want) < 0.051 for n in nums(line))


def line_with(out, word):
    hits = [ln for ln in out.splitlines() if re.search(r"\b" + word + r"\b", ln, re.I)]
    assert hits, f"no line with {word!r} in:\n{out}"
    return hits[0]


def write_tree(tmp_path, spec):
    root = tmp_path / "transcripts"
    W.write_transcripts(root, spec)
    return root


def ledger(tmp_path, spec, *args):
    assert LEDGER.exists(), f"{LEDGER.relative_to(REPO)} does not exist"
    root = write_tree(tmp_path, spec)
    r = subprocess.run([sys.executable, str(LEDGER), "--transcripts", str(root), "--project", W.SLUG, *args],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"exit {r.returncode}:\n{r.stdout}{r.stderr}"
    return r.stdout


def metrics(tmp_path, ids, transcripts, *, prices=None, approved=T.APPROVED, **opts):
    assert METRICS.exists()
    opts.setdefault("sdk_rows", [])
    w = W.build_world(tmp_path, transcripts=transcripts, thresholds=T.thresholds(approved, prices), **opts)
    r = subprocess.run([sys.executable, str(METRICS), *w["args"]], capture_output=True, text=True, timeout=300)
    got = {}
    for ln in r.stdout.splitlines():
        m = LINE.match(ln)
        if m:
            got[m.group(1)] = (m.group(2), ln)
    for i in ids:
        assert i in got, f"no METRIC {i} line in:\n{r.stdout}{r.stderr}"
    return r, got


def top(session, model, entries_by_day):
    return {f"{session}.jsonl": [T.tok(model, T.at(d, 10, k), m) for d, ms in entries_by_day.items() for k, m in enumerate(ms)]}


# ---------------------------------------------------------------- controls for the helpers (green now)
def test_0_number_reader_control():
    assert has("P0 | 3.8 | 5.00 | over", 5.0) and has("total 40.0 of 1,500", 1500) and not has("P0 3.8 5.0", 38)


def test_0_workflows_path_control_old_folder_counts_as_method_text_today(tmp_path):
    ex = [({"docs/northstar/plans/workflows_2026-10-07/wf.py": ("a", f"edit {i}\n")}, W.D["wed"]) for i in range(5)]
    w = W.build_world(tmp_path, extra_commits=ex)
    r = subprocess.run([sys.executable, str(METRICS), *w["args"]], capture_output=True, text=True, timeout=300)
    assert re.search(r"^METRIC M24a FAIL", r.stdout, re.M), r.stdout


# ---------------------------------------------------------------- 1 (A10: per day and per piece, planned against actual)
def test_1_ledger_day_rows_planned_actual_over_under_unplanned_coordinator(tmp_path):
    d1, d2 = "2026-11-02", "2026-11-03"
    plan = tmp_path / "plan.csv"
    plan.write_text("date,piece,role,estimate_m\n2026-11-02,P0,tests,3.8\n2026-11-02,P1,build,1.2\n2026-11-03,P2,land,1.6\n")
    spec = {
        **top("sess-arch", W.FABLE, {d1: [1.0, 1.0], d2: [3.0]}),
        **top("sess-disp", W.SONNET, {d1: [1.0, 1.0]}),
        **T.run_files("sess-disp", 1, "P0 tests", [T.tok(W.SONNET, T.at(d1), 5.0, sidechain=True)]),
        **T.run_files("sess-disp", 2, "P0 tests", [T.tok(W.SONNET, T.at(d2), 9.0, sidechain=True)]),  # other day: excluded
        **T.run_files("sess-disp", 3, "P1 build", [T.tok(W.SONNET, T.at(d1), 1.0, sidechain=True)]),
        **T.run_files("sess-disp", 4, "Z9 build", [T.tok(W.SONNET, T.at(d1), 0.7, sidechain=True)]),
        **T.run_files("sess-disp", 5, "lint fix", [T.tok(W.SONNET, T.at(d1), 0.3, sidechain=True)]),
    }
    out = ledger(tmp_path, spec, "--day", d1, "--plan", str(plan))
    p0, p1 = line_with(out, "P0"), line_with(out, "P1")
    assert has(p0, 3.8) and has(p0, 5.0) and re.search(r"\bover\b", p0, re.I) and not re.search(r"\bunder\b", p0, re.I), p0
    assert has(p1, 1.2) and has(p1, 1.0) and re.search(r"\bunder\b", p1, re.I) and not re.search(r"\bover\b", p1, re.I), p1
    assert not re.search(r"\bP2\b", out), "a plan row of another day must not print"
    assert has(line_with(out, "unplanned"), 1.0), line_with(out, "unplanned")
    assert has(line_with(out, "coordinator"), 4.0), line_with(out, "coordinator")


# ---------------------------------------------------------------- 2 (A10: week against the allotment, the split)
def test_2_ledger_week_total_against_allotment_and_split(tmp_path):
    toml = tmp_path / "th.toml"
    toml.write_text(T.thresholds())
    spec = {
        **top("sess-disp", W.SONNET, {"2026-11-02": [30.0], "2026-10-30": [50.0]}),  # 10-30 is W44: excluded
        **T.run_files("sess-disp", 1, "P0 build", [T.tok(W.SONNET, T.at("2026-11-03"), 10.0, sidechain=True)]),
    }
    out = ledger(tmp_path, spec, "--week", "2026-W45", "--thresholds", str(toml))
    tot = line_with(out, "total")
    assert has(tot, 40.0) and has(tot, 1500), tot
    for word, per_day in (("dispatcher", 60), ("pieces", 180), ("reserve", 60)):
        ln = line_with(out, word)
        assert has(ln, per_day) or has(ln, per_day * 5), f"{word} line lacks {per_day} (a day) or {per_day * 5} (the week): {ln}"


# ---------------------------------------------------------------- 3 (A10: the `[estimates]` table)
def test_3_estimates_table_per_task_type():
    th = tomllib.loads(TOML.read_text())
    est = th.get("estimates")
    assert est is not None, "method_thresholds.toml has no [estimates] table"
    assert set(est) == set(T.ESTIMATES), sorted(est)
    for task, (med, ceil, cap) in T.ESTIMATES.items():
        assert (est[task]["median_m"], est[task]["ceiling_m"], est[task]["calls_cap"]) == (med, ceil, cap), task


# ---------------------------------------------------------------- 4 (A10: M25 tokens per landed piece against its ceilings)
def m25_world(tests_m, build_m, land_m):
    sess = "sess-disp"
    return {
        **top(sess, W.SONNET, {W.D["wed"]: [0.1]}),
        **T.run_files(sess, 1, "P0 tests", [T.tok(W.SONNET, T.at(W.D["wed"]), tests_m, sidechain=True)]),
        **T.run_files(sess, 2, "P0 build", [T.tok(W.SONNET, T.at(W.D["wed"]), build_m, sidechain=True)]),
        **T.run_files(sess, 3, "P0 land", [T.tok(W.SONNET, T.at(W.D["wed"]), land_m, sidechain=True)]),
    }


def test_4_M25_fail_above_the_sum_of_ceilings(tmp_path):  # ceilings 16 + 6.3 + 5.5 = 27.8; runs 30
    r, got = metrics(tmp_path, ["M25"], m25_world(20.0, 6.0, 4.0))
    assert got["M25"][0] == "FAIL", got["M25"][1]
    assert r.returncode == 1


def test_4_M25_pass_under_the_sum_of_ceilings(tmp_path):  # runs 5.5 of 27.8
    r, got = metrics(tmp_path, ["M25"], m25_world(3.0, 1.0, 1.5))
    assert got["M25"][0] == "PASS", got["M25"][1]


# ---------------------------------------------------------------- 5 (A10: M26 week total, report only)
def test_5_M26_prints_NA_with_total_and_allotment(tmp_path):
    spec = {**top("sess-disp", W.SONNET, {W.D["wed"]: [12.0]}),
            **T.run_files("sess-disp", 1, "P0 build", [T.tok(W.SONNET, T.at(W.D["wed"]), 8.0, sidechain=True)])}
    r, got = metrics(tmp_path, ["M26"], spec)
    status, ln = got["M26"]
    assert status == "NA", ln
    assert has(ln, 20.0) and has(ln, 1500), ln


# ---------------------------------------------------------------- 6 (A10, DEC-coordinator-wakeups item 1: M27)
# test_6_M27_fail_three_text_only_turns_in_ten_events retired by HARNESS-mm-19 A17, ledger row TD-HARNESS-mm-19-M27
# (it asserted the old definition: FAIL at 3 text-only turns in 10 events; new cases: test_method_metrics.py test_a17_M27_*).
def test_6_M27_pass_one_in_ten_and_other_sessions_not_counted(tmp_path):
    # rewritten by HARNESS-mm-19 A17, ledger row TD-HARNESS-mm-19-M27 (was: text-only ratio 1 in 10).
    # Dispatcher: ten one-call episodes of 0.06 M each (PASS under the 1.0 M ceiling). A Fable (Architect) session with
    # ten 5.0 M episodes must not count: only the Dispatcher does (counting it would read 5.0 M, FAIL).
    arch = [W.clean(W.FABLE, T.at(W.D["wed"], 9, 0))]
    for i in range(10):
        arch += [T.event("task", T.at(W.D["wed"], 10, 2 * i)),
                 T.tok(W.FABLE, T.at(W.D["wed"], 10, 2 * i + 1), usage={"cache_read_input_tokens": 5_000_000})]
    spec = {"sess-disp.jsonl": T.dispatcher_episodes(1), "sess-arch.jsonl": arch}
    r, got = metrics(tmp_path, ["M27"], spec)
    assert got["M27"][0] == "PASS", got["M27"][1]
    assert " 0.06 vs" in got["M27"][1], got["M27"][1]  # has() tolerance 0.051 would also accept the old 0.1


# ---------------------------------------------------------------- 7 (A10, wakeups item 3: M28)
def sends(n, day, k0=0):
    return [W.entry(W.SONNET, T.at(day, 11, k0 + i), tools=[("SendMessage", {"to": "arch", "message": "m"})]) for i in range(n)]


def test_7_M28_fail_five_messages_in_one_session_day(tmp_path):
    spec = {"sess-disp.jsonl": [W.clean(W.SONNET, T.at(W.D["wed"], 9)), *sends(5, W.D["wed"])]}
    r, got = metrics(tmp_path, ["M28"], spec)
    assert got["M28"][0] == "FAIL", got["M28"][1]
    assert r.returncode == 1


def test_7_M28_pass_four_a_day_is_the_max_across_sessions_and_days(tmp_path):
    spec = {"sess-a.jsonl": [W.clean(W.SONNET, T.at(W.D["wed"], 9)), *sends(4, W.D["wed"]), *sends(3, W.D["thu"])],
            "sess-b.jsonl": [W.clean(W.SONNET, T.at(W.D["wed"], 9)), *sends(4, W.D["wed"])]}
    r, got = metrics(tmp_path, ["M28"], spec)
    assert got["M28"][0] == "PASS", got["M28"][1]


# ---------------------------------------------------------------- 8 (A10, wakeups item 4: M29)
def many_tests_runs(n):
    out = {}
    for i in range(n):
        out.update(T.run_files("sess-disp", i, "P0 tests", [T.tok(W.SONNET, T.at(W.D["wed"], 10, i), 0.01, sidechain=True)]))
    return out


def test_8_M29_fail_two_extra_tests_runs(tmp_path):  # three runs of role tests on P0, landed: 2 beyond the first
    r, got = metrics(tmp_path, ["M29"], many_tests_runs(3))
    assert got["M29"][0] == "FAIL", got["M29"][1]
    assert r.returncode == 1


def test_8_M29_pass_one_extra_tests_run(tmp_path):
    r, got = metrics(tmp_path, ["M29"], many_tests_runs(2))
    assert got["M29"][0] == "PASS", got["M29"][1]


# ---------------------------------------------------------------- 9 (A10: M06 and M07 include top-level session usage)
def test_9_M06_M07_price_top_level_sessions_by_model(tmp_path):
    # Fable top-level: 1 M in + 0.1 M out = $15; Sonnet audit sub-agent: 1 M in + 0.1 M out = $3. Without the top-level
    # session M06 reads 0% and M07 100%.
    use = {"usage": {"input_tokens": 1_000_000, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                     "output_tokens": 100_000}}
    spec = {"sess-arch.jsonl": [T.tok(W.FABLE, T.at(W.D["wed"]), **use)],
            **T.run_files("sess-disp", 1, "P0 audit", [T.tok(W.SONNET, T.at(W.D["wed"]), sidechain=True, **use)])}
    r, got = metrics(tmp_path, ["M06", "M07"], spec, prices=T.PRICES)
    m6 = re.match(r"METRIC M06 \S+ ([\d.]+)%", got["M06"][1])
    m7 = re.match(r"METRIC M07 \S+ ([\d.]+)%", got["M07"][1])
    assert m6 and 80 <= float(m6.group(1)) <= 87, got["M06"][1]
    assert m7 and 15 <= float(m7.group(1)) <= 18.5, got["M07"][1]


# ---------------------------------------------------------------- 10 (A10: METHOD_PATHS names the workflow scripts)
def test_10_method_paths_names_the_workflows_folder():
    sys.path.insert(0, str(SPEC))
    import method_metrics as mm
    assert "scripts/specfactory/workflows/" in mm.METHOD_PATHS, mm.METHOD_PATHS


def test_10_M24a_counts_a_workflow_script_commit_as_method_text(tmp_path):
    ex = [({"scripts/specfactory/workflows/wf.py": ("a", f"edit {i}\n")}, W.D["wed"]) for i in range(5)]
    w = W.build_world(tmp_path, extra_commits=ex)
    r = subprocess.run([sys.executable, str(METRICS), *w["args"]], capture_output=True, text=True, timeout=300)
    m = {mm.group(1): mm.group(2) for mm in map(LINE.match, r.stdout.splitlines()) if mm}
    assert m.get("M24a") == "FAIL", r.stdout


# ---------------------------------------------------------------- 11 (A13/A14: new tables start DRAFT)
def test_11_new_metric_tables_exist_and_are_draft():
    th = tomllib.loads(TOML.read_text())
    for mid in T.NEW:
        assert mid in th, f"{mid} table missing from method_thresholds.toml"
        assert th[mid].get("approved") == "", f"{mid} must start DRAFT (approved = \"\"), got {th[mid].get('approved')!r}"
