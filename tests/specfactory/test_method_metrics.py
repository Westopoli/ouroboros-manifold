# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design" and "The gaps" (G01 to G23), "Pieces and owners"
"""scripts/specfactory/method_metrics.py: for each metric one known-good world (PASS) and one known-bad world (the
spec's positive control, FAIL). Worlds are built by fixtures/method_metrics/mm_world.py (week 2026-W44, lab phase).
Case names carry the piece that makes them green: 1a (git and ledger), 1b (runs and transcripts), 1c (CLI, M16-M18,
tamper, --write, --last, the W43 self-check). Red on origin/main because the script does not exist.

Interfaces the fixtures fix (the spec leaves them open; listed in the tests writer's report): see mm_world.py header.
Also: M09 is assigned to no piece in the spec, tagged 1a here; the age in M17 is week-Sunday minus blame date in
days; the week's landed pieces are the labels of rc-0 gate rows; M10 counts the 0-line rows (spec control 0, 12, 30).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "method_metrics.py"
sys.path.insert(0, str(HERE / "fixtures" / "method_metrics"))
import mm_world as W  # noqa: E402

LINE = re.compile(r"^METRIC (\S+) (PASS|FAIL|DRAFT|NA) (.*)$")
FULL = re.compile(r"^METRIC \S+ (PASS|FAIL|DRAFT|NA) .+ vs [<>=]+\S* \S+ \(.*\) 2026-W44$")


def run(tmp_path, extra=(), cli=(), **opts):
    assert SCRIPT.exists(), f"{SCRIPT.relative_to(REPO)} does not exist"
    w = W.build_world(tmp_path, **opts)
    r = subprocess.run([sys.executable, str(SCRIPT), *w["args"], *extra, *cli], capture_output=True, text=True,
                       timeout=300)
    got = {}
    for ln in r.stdout.splitlines():
        m = LINE.match(ln)
        if m:
            got[m.group(1)] = (m.group(2), ln)
    return r, got, w


def expect(tmp_path, ids, status, cli=(), **opts):
    r, got, w = run(tmp_path, cli=cli, **opts)
    for i in ids:
        assert i in got, f"no METRIC {i} line in:\n{r.stdout}{r.stderr}"
        assert got[i][0] == status, f"{i}: wanted {status}, got: {got[i][1]}"
    if status == "FAIL":
        assert r.returncode == 1, f"exit {r.returncode}, wanted 1 on a FAIL"
    return r, got, w


def led(*rows):
    return list(W.GOOD_LEDGER_WEEK) + list(rows)


def td(n, fable=0):
    return [f"| day40 | TD-x{i} ruler={'fable' if i < fable else 'clerk'} | d |" for i in range(n)]


def gate(*specs):
    """specs: dicts over a good row."""
    base = ["2026-10-28", "P0", "push/p0", "a" * 40, "b" * 40, 600, 1800, 0, "", "", 100, 100, 0, 20]
    rows = []
    for s in specs:
        row = list(base)
        for k, v in s.items():
            row[W.GATE_COLS.index(k)] = v
        rows.append(row)
    return rows


def sdk(*rows):
    return [(W.D["wed"], f"{p} {r}", p, r, m, 10, c, o) for p, r, m, c, o in rows]


# ============================================================ the good week
def test_1c_good_week_all_pass_or_na_exit_0(tmp_path):
    r, got, w = run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    for mid in W.TH:
        assert mid in got, f"no METRIC {mid} line"
    bad = {k: v[1] for k, v in got.items() if v[0] in ("FAIL", "DRAFT")}
    assert not bad, bad
    assert all(FULL.match(v[1]) for k, v in got.items() if k != "M17"), "METRIC line format"


# ============================================================ 1a: git and ledger
def test_1a_M01_pass(tmp_path):
    expect(tmp_path, ["M01"], "PASS")


def test_1a_M01_fail_ratio_2(tmp_path):  # spec G01 control: 300 game lines, 600 test lines
    expect(tmp_path, ["M01"], "FAIL", prod_commits=3, prod_lines=100, test_lines=200)


def test_1a_M01_ignores_fixture_lines(tmp_path):  # G22: 5,000 fixture lines do not move the ratio
    expect(tmp_path, ["M01"], "PASS", extra_commits=[({"tests/fixtures/big.json": 5000}, W.D["wed"])])


def test_1a_M01_na_under_200_game_lines(tmp_path):
    expect(tmp_path, ["M01"], "NA", prod_commits=1, prod_lines=100, test_lines=900)


def test_1a_M02_pass(tmp_path):
    expect(tmp_path, ["M02", "M02b"], "PASS")


def test_1a_M02_fail_12_td_4_landings(tmp_path):  # G02 control
    expect(tmp_path, ["M02", "M02b"], "FAIL", ledger_week=td(12, fable=3))


def test_1b_M03_pass(tmp_path):
    expect(tmp_path, ["M03"], "PASS", ledger_week=td(2, fable=2))


def test_1b_M03_fail_three_fable(tmp_path):
    expect(tmp_path, ["M03"], "FAIL", ledger_week=td(12, fable=3))


def test_1a_M04_pass(tmp_path):
    expect(tmp_path, ["M04"], "PASS")


def test_1a_M04_fail_40_docs_10_product(tmp_path):  # G03 control, ratio 4.0
    r, got, w = expect(tmp_path, ["M04"], "FAIL", docs_commits=40, prod_commits=10)
    assert "4.0" in got["M04"][1] and "40" in got["M04"][1] and "10" in got["M04"][1], got["M04"][1]


def test_1a_M05_pass(tmp_path):
    expect(tmp_path, ["M05", "M05b"], "PASS")


def test_1a_M05_fail_20_rows_4_landings(tmp_path):
    expect(tmp_path, ["M05"], "FAIL", ledger_week=[f"| day40 | NOTE-{i} | d |" for i in range(20)])


def test_1a_M05b_fail_three_drafts(tmp_path):
    expect(tmp_path, ["M05b"], "FAIL", ledger_week=led("| day40 | DRAFT-a | d |", "| day40 | DRAFT-b | d |"))


def test_1a_M09_pass(tmp_path):
    expect(tmp_path, ["M09", "M09b", "M09c"], "PASS")


def test_1a_M09_fail_two_timeouts(tmp_path):  # G06 control
    rows = gate({"rc": 1, "reject_stages": "regression_csim", "reject_causes": "suite-timeout 600s"},
                {"rc": 1, "reject_stages": "specfactory_regression", "reject_causes": "suite-timeout 600s"},
                {"stage_s": 4000, "queue_s": 7680})
    expect(tmp_path, ["M09", "M09b", "M09c"], "FAIL", gate_rows=rows)


def test_1a_M10_pass(tmp_path):
    expect(tmp_path, ["M10", "M10b"], "PASS")


def test_1a_M10_fail_median_small(tmp_path):  # G07 control: lines 0, 12, 30 (and 20 so a strict reading has 3 rows)
    expect(tmp_path, ["M10"], "FAIL",
           gate_rows=gate({"product_lines": 0}, {"product_lines": 12}, {"product_lines": 20}, {"product_lines": 30}))


def test_1a_M10b_fail_one_row_over_1000(tmp_path):
    expect(tmp_path, ["M10b"], "FAIL",
           gate_rows=gate({"product_lines": 100}, {"product_lines": 100}, {"product_lines": 100},
                          {"product_lines": 1200}))


def test_1a_M10_na_under_three_rows(tmp_path):
    expect(tmp_path, ["M10"], "NA", gate_rows=gate({"product_lines": 5}, {"product_lines": 5}))


def test_1a_M11_pass(tmp_path):
    expect(tmp_path, ["M11", "M11b", "M11c"], "PASS")


def test_1a_M11_fail_md_over_product(tmp_path):  # G08 control
    expect(tmp_path, ["M11"], "FAIL", extra_commits=[({"docs/northstar/plans/big.md": 2000}, W.D["wed"])])


def test_1a_M11_na_in_a_retro_week(tmp_path):
    expect(tmp_path, ["M11"], "NA", extra_commits=[
        ({"docs/northstar/plans/big.md": 2000, "docs/northstar/plans/retro_2026-10-27/README.md": 5}, W.D["wed"])])


def test_1a_M11b_fail_claude_130_lines(tmp_path):
    expect(tmp_path, ["M11b"], "FAIL", claude_lines=130)


def test_1a_M11c_fail_png_under_plans(tmp_path):
    expect(tmp_path, ["M11c"], "FAIL", extra_commits=[({"docs/northstar/plans/shot.png": "png\n"}, W.D["wed"])])


def test_1a_M11c_data_dir_is_excluded(tmp_path):
    expect(tmp_path, ["M11c"], "PASS",
           extra_commits=[({"docs/northstar/research/x/data/shot.png": "png\n"}, W.D["wed"])])


BETA_GOOD = "# Beta\nApproved: Westley 2026-11-01\n\n" + "".join(f"| S-{i:03d} | e | w |\n" for i in range(1, 21))
BETA_BAD = "# Beta\nApproved: Westley 2026-11-01\n\n" + "".join(f"| S-{i:03d} | e | w |\n" for i in range(1, 31))


def test_1a_M12_pass_beta(tmp_path):
    expect(tmp_path, ["M12a", "M12b", "M12c"], "PASS", phase="beta", beta_list=BETA_GOOD)


def test_1a_M12_na_in_lab(tmp_path):
    expect(tmp_path, ["M12a", "M12b", "M12c"], "NA", phase="lab", beta_list=BETA_GOOD)


def test_1a_M12_fail_30_rows_3_of_6_on_it(tmp_path):  # G09 control; pieces P3..P5 carry stories off the list
    pieces = [{"id": f"P{i}", "owns": [f"csrc/sim_{i}.c"], "story": f"S-00{i + 1}" if i < 3 else f"S-9{i}"}
              for i in range(6)]
    expect(tmp_path, ["M12a", "M12b"], "FAIL", phase="beta", beta_list=BETA_BAD, prod_commits=6, pieces=pieces)


def test_1a_M19_pass(tmp_path):
    expect(tmp_path, ["M19a", "M19b", "M19c"], "PASS")


def test_1a_M19a_fail_untagged_finding(tmp_path):  # G17 control (pre-2026-10-26 untagged rows in the base are ignored)
    expect(tmp_path, ["M19a"], "FAIL", ledger_week=led("| day40 | FINDING-bare | no token |"))


def test_1a_M19a_fail_td_without_ruler(tmp_path):
    expect(tmp_path, ["M19a"], "FAIL", ledger_week=led("| day40 | TD-bare | no token |"))


def test_1a_M19b_fail_string_status(tmp_path):
    p = W.default_pieces(4) + [{"id": "Pstr", "owns": ["csrc/z.c"], "status": ("s", "attached")}]
    expect(tmp_path, ["M19b"], "FAIL", pieces=p)


def test_1a_M19c_fail_commit_without_gate_row(tmp_path):  # two product commits, one gate row
    r, got, w = run(tmp_path, prod_commits=2, gate_rows="auto")
    rows = [x for x in (tmp_path / "gate_runs.csv").read_text().splitlines()]
    (tmp_path / "gate_runs.csv").write_text("\n".join(rows[:2]) + "\n")  # header + first row only
    r = subprocess.run([sys.executable, str(SCRIPT), *w["args"]], capture_output=True, text=True, timeout=300)
    m = [ln for ln in r.stdout.splitlines() if ln.startswith("METRIC M19c ")]
    assert m and m[0].split()[2] == "FAIL", r.stdout + r.stderr
    assert r.returncode == 1


def test_1a_M20_pass(tmp_path):
    expect(tmp_path, ["M20"], "PASS")


def test_1a_M20_fail_three_client_only_of_five(tmp_path):  # G18 control (lab_lines 0, product_lines > 0)
    rows = gate({}, {}, {"lab_lines": 0}, {"lab_lines": 0}, {"lab_lines": 0})
    expect(tmp_path, ["M20"], "FAIL", gate_rows=rows)


def test_1a_M23_pass(tmp_path):
    expect(tmp_path, ["M23"], "PASS")


def test_1a_M23_fail_golden_json(tmp_path):  # G22 control
    expect(tmp_path, ["M23"], "FAIL", extra_commits=[({"tests/csim/golden_x.json": "{}\n"}, W.D["wed"])])


def test_1a_M24_pass(tmp_path):
    expect(tmp_path, ["M24a", "M24b"], "PASS")


def test_1a_M24a_fail_five_method_commits_no_retro(tmp_path):  # G23 control
    ex = [({"CLAUDE.md": ("a", f"edit {i}\n")}, W.D["wed"]) for i in range(5)]
    expect(tmp_path, ["M24a"], "FAIL", extra_commits=ex)


def test_1a_M24a_pass_when_the_commit_adds_a_retro_path(tmp_path):
    ex = [({"CLAUDE.md": ("a", f"edit {i}\n"), f"docs/northstar/plans/retro_r{i}/n.md": 1}, W.D["wed"])
          for i in range(1)]
    expect(tmp_path, ["M24a"], "PASS", extra_commits=ex)


def test_1a_M24b_fail_two_retro_folders_in_10_days(tmp_path):
    ex = [({"docs/northstar/plans/retro_a/n.md": 1}, W.D["tue"]), ({"docs/northstar/plans/retro_b/n.md": 1}, W.D["fri"])]
    expect(tmp_path, ["M24b"], "FAIL", extra_commits=ex)


# ============================================================ 1b: runs and transcripts
def test_1b_M01b_pass(tmp_path):
    expect(tmp_path, ["M01b"], "PASS")


def test_1b_M01b_fail_tests_run_on_scenes_only_piece(tmp_path):
    rows = W.default_sdk(4) + sdk(("PS", "tests", W.SONNET, 1.0, "success"))
    expect(tmp_path, ["M01b"], "FAIL", sdk_rows=rows)


def test_1b_M06_pass(tmp_path):
    expect(tmp_path, ["M06", "M06b"], "PASS")


def test_1b_M06_fail_fable_60_of_90(tmp_path):  # G04 control
    rows = sdk(("P0", "build", W.FABLE, 60.0, "success"), ("P1", "build", W.SONNET, 30.0, "success"))
    expect(tmp_path, ["M06"], "FAIL", sdk_rows=rows)


def test_1b_M06b_fail_fable_draft_on_non_contract_piece(tmp_path):
    rows = W.default_sdk(4) + sdk(("P1", "draft", W.FABLE, 1.0, "success"))
    expect(tmp_path, ["M06b"], "FAIL", sdk_rows=rows)


def test_1b_M06b_pass_fable_draft_on_contract_piece(tmp_path):
    p = W.default_pieces(4) + [{"id": "CONTRACT-c", "owns": ["csrc/ouroboros_sim.h"], "contract": True,
                                "status": "attached"}]
    rows = W.default_sdk(4) + sdk(("CONTRACT-c", "draft", W.FABLE, 1.0, "success"))
    expect(tmp_path, ["M06b"], "PASS", pieces=p, sdk_rows=rows)


def test_1b_M07_pass(tmp_path):
    expect(tmp_path, ["M07", "M07b"], "PASS")


def test_1b_M07_fail_audit_9_of_100(tmp_path):  # G19 control
    rows = sdk(("P0", "build", W.SONNET, 91.0, "success"), ("P0", "audit", W.SONNET, 9.0, "success"))
    expect(tmp_path, ["M07", "M07b"], "FAIL", sdk_rows=rows)


def test_1b_M07b_fail_verify_run(tmp_path):
    rows = W.default_sdk(4) + sdk(("P0", "verify", W.SONNET, 0.1, "success"))
    expect(tmp_path, ["M07b"], "FAIL", sdk_rows=rows)


def big_call_session(model, ctx, n=1):
    return [W.clean(model, W.ts(11, m)) for m in range(3)] + [W.entry(model, W.ts(11, 10 + m), ctx=ctx) for m in range(n)]


def test_1b_M08_pass(tmp_path):
    expect(tmp_path, ["M08", "M08b"], "PASS")


def test_1b_M08_fail_one_450k_call(tmp_path):  # G05 control
    t = W.default_transcripts()
    t["sess-big.jsonl"] = big_call_session(W.SONNET, 450000)
    expect(tmp_path, ["M08"], "FAIL", transcripts=t)


def sleep_turn(model, minute):
    return W.entry(model, W.ts(12, minute), tools=[("Bash", {"command": "sleep 60 && ls"})])


def test_1b_M08b_fail_two_polling_turns(tmp_path):
    t = W.default_transcripts()
    t["sess-poll.jsonl"] = [W.clean(W.SONNET, W.ts(12, 0)), sleep_turn(W.SONNET, 1), sleep_turn(W.SONNET, 2)]
    expect(tmp_path, ["M08b"], "FAIL", transcripts=t)


def test_1b_M13_pass(tmp_path):
    expect(tmp_path, ["M13", "M13b"], "PASS")


def test_1b_M13_fail_four_landing_runs_on_one_piece(tmp_path):  # G10 control
    rows = W.default_sdk(4) + sdk(*[("P0", "land", W.SONNET, 1.0, "success")] * 3)
    expect(tmp_path, ["M13"], "FAIL", sdk_rows=rows)


def test_1b_M13b_fail_landing_costs_more_than_building(tmp_path):
    rows = sdk(("P0", "build", W.SONNET, 2.0, "success"), ("P0", "land", W.SONNET, 5.0, "success"),
               ("P0", "land", W.SONNET, 5.0, "success"))
    expect(tmp_path, ["M13b"], "FAIL", sdk_rows=rows)


def test_1b_M14_pass(tmp_path):
    expect(tmp_path, ["M14", "M14b"], "PASS")


def test_1b_M14_fail_seven_runs_with_records_and_verify(tmp_path):  # G11 control (one landed piece)
    rows = sdk(*[("P0", r, W.SONNET, 1.0, "success") for r in
                 ("spec", "tests", "build", "land", "records", "verify", "land")])
    expect(tmp_path, ["M14", "M14b"], "FAIL", prod_commits=1, sdk_rows=rows)


def test_1b_M14_subagent_meta_runs_are_joined(tmp_path):
    """Runs come from sub-agent meta (description `<piece> <role>`), model and RESULT line from the agent file."""
    t = W.default_transcripts()
    for k, role in enumerate(("spec", "tests", "build", "land", "records", "verify", "land")):
        t[f"sess-disp/subagents/agent-m{k}.jsonl"] = [W.entry(W.SONNET, W.ts(10, k), text="RESULT success")]
        t[f"sess-disp/subagents/agent-m{k}.meta.json"] = {"agentType": "engineer", "description": f"P0 {role}"}
    t.pop("sess-disp/subagents/agent-sub1.meta.json")
    t.pop("sess-disp/subagents/agent-sub1.jsonl")
    expect(tmp_path, ["M14", "M14b"], "FAIL", prod_commits=1, sdk_rows=[], transcripts=t)


def test_1b_M15_pass(tmp_path):
    expect(tmp_path, ["M15"], "PASS")


def test_1b_M15_fail_four_stops_of_ten(tmp_path):  # G12 control
    rows = sdk(*[("P0", "build", W.SONNET, 1.0, "success")] * 6, *[("P0", "build", W.SONNET, 1.0, "stop:spec")] * 4)
    expect(tmp_path, ["M15"], "FAIL", sdk_rows=rows)


def test_1b_M21_pass(tmp_path):
    expect(tmp_path, ["M21a", "M21b"], "PASS")


def test_1b_M21a_fail_two_exc_rows(tmp_path):  # G20 control
    expect(tmp_path, ["M21a"], "FAIL", ledger_week=led("| day40 | EXC-a | d |", "| day40 | EXC-b | d |"))


def test_1b_M21b_fail_three_drift_turns(tmp_path):
    t = W.default_transcripts()
    t["sess-drift.jsonl"] = [
        W.entry(W.SONNET, W.ts(13, 0), tools=[("ScheduleWakeup", {"delaySeconds": 270, "reason": "p"})]),
        sleep_turn(W.SONNET, 1),
        W.entry(W.SONNET, W.ts(13, 2), tools=[("Agent", {"subagent_type": "engineer", "prompt": "x"})])]
    expect(tmp_path, ["M21b"], "FAIL", transcripts=t)


def test_1b_M22_pass_two_sessions_and_a_subagent_in_one_hour(tmp_path):
    expect(tmp_path, ["M22"], "PASS")


def test_1b_M22_fail_three_coordinator_sessions(tmp_path):  # G21 control: two Fable, one Sonnet
    t = W.default_transcripts()
    t["sess-arch2.jsonl"] = [W.clean(W.FABLE, W.ts(10, m)) for m in range(3)]
    expect(tmp_path, ["M22"], "FAIL", transcripts=t)


# ============================================================ 1c: M16-M18, CLI
def test_1c_M16_pass(tmp_path):
    expect(tmp_path, ["M16"], "PASS")


def test_1c_M16_fail_three_look_pieces_no_verdict(tmp_path):  # G13 control
    p = W.default_pieces(4) + [{"id": "VG-X-c", "owns": ["scenes/x/c.gd"], "status": "attached"}]
    expect(tmp_path, ["M16"], "FAIL", pieces=p, readme_rows=())


def test_1c_M17_prints_open_rows_and_age_never_fails(tmp_path):  # G14 control
    r, got, w = run(tmp_path, readme_open=3)
    assert "M17" in got, r.stdout
    assert got["M17"][0] == "NA" and "3 rows, oldest 12 d" in got["M17"][1], got["M17"][1]


def test_1c_M18_pass(tmp_path):
    expect(tmp_path, ["M18a", "M18b", "M18c", "M18d"], "PASS")


def test_1c_M18a_fail_14_active(tmp_path):  # G15 control
    expect(tmp_path, ["M18a"], "FAIL", wt_active=14)


def test_1c_M18b_fail_21_done_not_reaped(tmp_path):
    expect(tmp_path, ["M18b"], "FAIL", wt_done=21)


def test_1c_M18c_fail_over_the_disk_cap(tmp_path):  # cap lowered to 0.001 GB for a 5 MB tree
    th = W.thresholds_toml(override={"M18c": {"value": 0.001}})
    expect(tmp_path, ["M18c"], "FAIL", thresholds=th, wt_extra_mb=5)


def test_1c_M18d_fail_12_stale_unmerged_branches(tmp_path):
    expect(tmp_path, ["M18d"], "FAIL", old_branches=12)


def test_1c_tamper_unapproved_threshold_prints_draft_never_pass(tmp_path):
    r, got, w = run(tmp_path, thresholds=W.thresholds_toml(approved=""))
    assert got.get("M04", ("",))[0] == "DRAFT", r.stdout + r.stderr
    assert not [k for k, v in got.items() if v[0] == "PASS"], "a PASS with an unapproved threshold"


def test_1c_tamper_one_unapproved_threshold_only_that_metric_is_draft(tmp_path):
    th = W.thresholds_toml(override={"M04": {"approved": ""}})
    r, got, w = run(tmp_path, thresholds=th)
    assert got["M04"][0] == "DRAFT" and got["M23"][0] == "PASS", r.stdout


def test_1c_write_stores_the_week_json_and_a_readme_row(tmp_path):
    r, got, w = run(tmp_path, extra=["--write"])
    j = w["repo"] / W.METRICS_DIR / "2026-W44.json"
    assert j.is_file(), f"{j} not written\n{r.stdout}{r.stderr}"
    assert "M04" in j.read_text()
    assert "2026-W44" in (w["repo"] / W.METRICS_DIR / "README.md").read_text()


def test_1c_last_prints_the_fail_lines_of_the_latest_stored_week(tmp_path):
    r, got, w = run(tmp_path, extra=["--write"], docs_commits=40, prod_commits=10)
    assert got["M04"][0] == "FAIL"
    r2 = subprocess.run([sys.executable, str(SCRIPT), "--last", "--repo", str(w["repo"])], capture_output=True,
                        text=True, timeout=120)
    assert any(ln.startswith("METRIC M04 FAIL") for ln in r2.stdout.splitlines()), r2.stdout + r2.stderr


def _statuses(obj, out=None):
    out = {} if out is None else out
    if isinstance(obj, dict):
        if "id" in obj and "status" in obj:
            out[obj["id"]] = obj["status"]
        for k, v in obj.items():
            if isinstance(v, str) and re.fullmatch(r"M\d\d[a-d]?", k) and v in ("PASS", "FAIL", "DRAFT", "NA"):
                out[k] = v
            else:
                _statuses(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _statuses(v, out)
    return out


def test_1c_w43_snapshot_trips_the_bad_week_metrics():
    p = REPO / "docs/northstar/plans/method_rev3_2026-10-26/metrics/2026-W43.json"
    assert p.is_file(), f"{p.relative_to(REPO)} does not exist"
    st = _statuses(json.loads(p.read_text()))
    for prefix in ("M04", "M06", "M09", "M18", "M19"):
        assert any(k.startswith(prefix) and v == "FAIL" for k, v in st.items()), f"{prefix} not FAIL in {st}"


# ============================================================ controls (green without the script)
def test_control_good_world_builds_and_its_dates_are_inside_the_week(tmp_path):
    w = W.build_world(tmp_path)
    log = W.sh(w["repo"], "git", "log", "origin/main", "--since=2026-10-26", "--until=2026-11-02", "--format=%H")
    assert len(log.split()) >= 9
    stale = W.sh(w["repo"], "git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin/push/").split()
    assert len(stale) == 2
    merged = W.sh(w["repo"], "git", "branch", "-r", "--merged", "origin/main")
    assert "push/stale" not in merged
    assert (w["wt"] / "a0" / ".wt-state").read_text().startswith("active ")


def test_control_thresholds_toml_parses_with_every_metric():
    import tomllib
    d = tomllib.loads(W.thresholds_toml())
    assert set(W.TH) <= set(d) and d["M04"]["approved"] == "2026-10-26"
    assert tomllib.loads(W.thresholds_toml(approved=""))["M04"]["approved"] == ""
