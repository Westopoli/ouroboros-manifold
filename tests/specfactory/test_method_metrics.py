# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design" and "The gaps" (G01 to G23), "Pieces and owners"
"""scripts/specfactory/method_metrics.py: for each metric one known-good world (PASS) and one known-bad world (the
spec's positive control, FAIL). Worlds are built by fixtures/method_metrics/mm_world.py (week 2026-W44, lab phase).
Case names carry the piece that makes them green: 1a (git and ledger), 1b (runs and transcripts), 1c (CLI, M16-M18,
tamper, --write, --last, the W43 self-check). Red on origin/main because the script does not exist.

Interfaces the fixtures fix (the spec leaves them open; listed in the tests writer's report): see mm_world.py header.
Phase 4 (HARNESS-mm-8/mm-9, audit_findings.md): the cases named `test_<finding>_...` at the end of the file are the
audit-finding tests; the fixture world now carries the real gate csv header, transcripts under the default project
folder, the new README table and a verdicts file (see mm_world.py). Also: M09 is assigned to no piece in the spec, tagged 1a here; the age in M17 is week-Sunday minus blame date in
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


def test_1a_M04_fail_40_docs_10_product(tmp_path):  # G03 control, ratio 4.3 (43 docs-only commits)
    r, got, w = expect(tmp_path, ["M04"], "FAIL", docs_commits=40, prod_commits=10)
    assert "4.3" in got["M04"][1] and "43" in got["M04"][1] and "10" in got["M04"][1], got["M04"][1]


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
    expect(tmp_path, ["M16"], "FAIL", pieces=p, readme_rows=(), verdicts_text="")


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


# RETIRED by audit finding 3 (HARNESS-mm-8): test_1c_w43_snapshot_trips_the_bad_week_metrics read the stored
# 2026-W43.json and never ran the script, so a script gone blind stayed green; the self-check is
# test_9_self_check_runs_the_script_on_the_bad_world below (a subprocess on the bad fixture world).


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


# ============================================================ Phase 4: the audit findings
# spec: docs/northstar/plans/method_rev3_2026-10-26/audit_findings.md (finding numbers in each name) and spec.md A9.
# Tests the finding retires: test_1c_w43_snapshot_trips_the_bad_week_metrics (finding 3, replaced by test_3_35_*);
# test_1c_M16_fail_three_look_pieces_no_verdict gained verdicts_text="" (finding 17); the fixture's gate header,
# README table, transcript folder and verdicts file changed (findings 1, 5, 17, 32), so every case that reads
# those is red on origin/main until mm-8 reads the real shapes. Interfaces these cases fix beyond the audit table:
# [prices."<model id>"] tables with input, cache_read, cache_write, output (dollars per million tokens, as the
# mm-8 brief says); a [M15] key max_unknown (percent); the id M11b-bytes (its own [M11b-bytes] table);
# transcripts folder = --project (default: the repo's slug, mm_world.SLUG); `--weeks A..B` for the back-test.
REAL_GATE_CSV = REPO / "docs/northstar/plans/push/gate_runs.csv"


def spawn(t, name, desc, model=None, result="RESULT success", entries=None, minute=5):
    """A sub-agent run as the parser sees it: meta description plus a transcript with a RESULT line."""
    t[f"sess-disp/subagents/agent-{name}.jsonl"] = entries or [W.entry(model or W.SONNET, W.ts(10, minute), text=result)]
    t[f"sess-disp/subagents/agent-{name}.meta.json"] = {"agentType": "engineer", "description": desc}
    return t


def detail(line):
    return line[line.index("(") + 1:line.rindex(")")]


# ---- finding 1: the gate csv header
def test_1_fixture_gate_header_is_the_real_header(tmp_path):
    real = REAL_GATE_CSV.read_text().splitlines()[0]
    assert real.startswith("date,label,branch,base_sha,candidate_sha,queue_s,"), real
    w = W.build_world(tmp_path)
    assert (tmp_path / "gate_runs.csv").read_text().splitlines()[0] == real, "fixture header differs from the real one"


def test_1_one_rc0_row_on_main_gives_M19c_pass_not_a_traceback(tmp_path):
    r, got, w = run(tmp_path, prod_commits=1)
    assert "Traceback" not in r.stderr, r.stderr[-500:]
    assert "M19c" in got and got["M19c"][0] in ("PASS", "DRAFT"), r.stdout + r.stderr[-500:]


# ---- findings 3, 35: the self-check runs the script on the bad world; --baseline is gone
BAD_FAIL_SET = ["M01", "M02b", "M04", "M05b", "M11c", "M16", "M18b", "M19c", "M24a", "M24b"]


def bad_world_opts():
    extra = [({"docs/northstar/plans/shot.png": "png\n"}, W.D["wed"])]
    extra += [({"CLAUDE.md": ("a", f"edit {i}\n")}, W.D["wed"]) for i in range(5)]
    extra += [({"docs/northstar/plans/retro_a/n.md": 1}, W.D["tue"]), ({"docs/northstar/plans/retro_b/n.md": 1}, W.D["fri"])]
    return dict(prod_commits=4, prod_lines=100, test_lines=200, docs_commits=40, gate_rows=[], wt_done=21,
                ledger_week=td(12, fable=3) + [f"| day40 | DRAFT-{c} | d |" for c in "abc"],
                pieces=W.default_pieces(4) + [{"id": "VG-X-c", "owns": ["scenes/x/c.gd"], "status": "attached"}],
                readme_rows=(), verdicts_text="", extra_commits=extra)


def test_3_35_self_check_runs_the_script_on_the_bad_world(tmp_path):
    r, got, w = expect(tmp_path, BAD_FAIL_SET, "FAIL", **bad_world_opts())
    assert r.returncode == 1


@pytest.mark.parametrize("flag", [["--baseline", "M04"], ["--baseline", "M06,M09"], ["--no-such-flag"]])
def test_3_unknown_arguments_and_the_removed_baseline_flag_are_rejected(tmp_path, flag):
    w = W.build_world(tmp_path)
    r = subprocess.run([sys.executable, str(SCRIPT), *w["args"], *flag], capture_output=True, text=True, timeout=120)
    assert r.returncode == 2 and "unrecognized arguments" in r.stderr, f"exit {r.returncode}: {r.stderr[-300:]}"


# ---- finding 4: one judge, FAIL stays FAIL for runs-side metrics
def test_4_unapproved_runs_metric_with_a_failing_value_prints_fail_and_exits_1(tmp_path):
    t = W.default_transcripts()
    t["sess-big.jsonl"] = big_call_session(W.SONNET, 450000)
    th = W.thresholds_toml(override={"M08": {"approved": ""}})
    r, got, w = run(tmp_path, transcripts=t, thresholds=th)
    assert got["M08"][0] == "FAIL", got["M08"][1]
    assert r.returncode == 1


def test_4_control_unapproved_runs_metric_that_passes_prints_draft(tmp_path):
    r, got, w = run(tmp_path, thresholds=W.thresholds_toml(override={"M08": {"approved": ""}}))
    assert got["M08"][0] == "DRAFT", got["M08"][1]


# ---- finding 5: only the named project folder is counted
JARVIS_DIR = "-home-westopoli-Projects-Jarvis"


def test_5_only_the_default_project_folder_is_counted_by_M08(tmp_path):
    t = W.default_transcripts()
    t[f"!{JARVIS_DIR}/sess-jarvis.jsonl"] = big_call_session(W.SONNET, 450000)
    expect(tmp_path, ["M08"], "PASS", transcripts=t)


def test_5_project_flag_names_the_folder_that_is_counted(tmp_path):
    t = W.default_transcripts()
    t[f"!{JARVIS_DIR}/sess-jarvis.jsonl"] = big_call_session(W.SONNET, 450000)
    # the = form: a slug starting with - is not a separate value to argparse
    r, got, w = run(tmp_path, cli=[f"--project={JARVIS_DIR}"], transcripts=t)
    assert got["M08"][0] == "FAIL" and ": 1," in got["M08"][1], got["M08"][1]


# ---- finding 6: a coordinator spawns or is Fable
def test_6_three_worker_sonnet_sessions_in_one_hour_give_zero(tmp_path):
    t = {f"w{i}.jsonl": [W.entry(W.SONNET, W.ts(10, m)) for m in range(3)] for i in range(3)}
    r, got, w = run(tmp_path, transcripts=t)
    assert re.match(r"METRIC M22 PASS 0 vs", got["M22"][1]), got["M22"][1]


def test_6_fable_sessions_count_even_without_a_spawn(tmp_path):
    t = {f"f{i}.jsonl": [W.entry(W.FABLE, W.ts(10, m)) for m in range(3)] for i in range(3)}
    expect(tmp_path, ["M22"], "FAIL", transcripts=t)


@pytest.mark.parametrize("tool", ["Agent", "SendMessage"])
def test_6_a_sonnet_session_that_spawns_or_messages_counts(tmp_path, tool):
    t = {f"s{i}.jsonl": [W.entry(W.SONNET, W.ts(10, m), tools=[(tool, {"prompt": "x", "model": "sonnet"})])
                         for m in range(3)] for i in range(3)}
    expect(tmp_path, ["M22"], "FAIL", transcripts=t)


# ---- finding 7: client-only means every non-tests owns path is under autoload/ or scenes/
def test_7_M01b_flags_a_scenes_piece_that_also_owns_a_tests_path(tmp_path):
    p = W.default_pieces(4) + [{"id": "PL", "owns": ["scenes/x/l.gd", "tests/qa/test_l.py"], "status": "landed"}]
    rows = W.default_sdk(4) + sdk(("PL", "tests", W.SONNET, 1.0, "success"))
    expect(tmp_path, ["M01b"], "FAIL", pieces=p, sdk_rows=rows)


def test_7_control_M01b_passes_when_the_piece_also_owns_csrc(tmp_path):
    p = W.default_pieces(4) + [{"id": "PL", "owns": ["scenes/x/l.gd", "csrc/l.c", "tests/qa/test_l.py"], "status": "landed"}]
    rows = W.default_sdk(4) + sdk(("PL", "tests", W.SONNET, 1.0, "success"))
    expect(tmp_path, ["M01b"], "PASS", pieces=p, sdk_rows=rows)


# ---- finding 8: transcript runs are priced from [prices]
PRICES = {W.FABLE: {"input": 10.0, "cache_read": 1.0, "cache_write": 10.0, "output": 50.0},
          W.SONNET: {"input": 3.0, "cache_read": 0.3, "cache_write": 3.75, "output": 15.0}}


def test_8_priced_fable_transcript_run_has_a_cost_and_M06_prints_a_percentage(tmp_path):
    # five Fable calls of 1,000,000 tokens (1000 in, 998,500 cache read, 500 cache write, 200 out) = $5.1175,
    # plus the default sub-agent's $0.0835, over the sdk rows' $20 of Sonnet: about 20.6%
    t = W.default_transcripts()
    spawn(t, "fab", "P1 build", entries=[W.entry(W.FABLE, W.ts(10, m), ctx=1000000, text="RESULT success") for m in range(5)])
    r, got, w = run(tmp_path, transcripts=t, thresholds=W.thresholds_toml(prices=PRICES))
    m = re.match(r"METRIC M06 \S+ ([\d.]+)%", got["M06"][1])
    assert m and 19 <= float(m.group(1)) <= 22, got["M06"][1]


# ---- finding 9: only `<pieces.toml id> <role>` is a labelled run
def test_9_a_fresh_audit_spawn_is_an_unlabelled_run_that_M14b_counts(tmp_path):
    t = spawn(W.default_transcripts(), "fa", "Fresh audit")
    r, got, w = expect(tmp_path, ["M14b"], "FAIL", transcripts=t)
    assert "unlabelled" in got["M14b"][1], got["M14b"][1]
    assert got["M07b"][0] == "PASS", "'Fresh' is not a piece id, so this is not an audit run on a piece: " + got["M07b"][1]


def test_9_a_spawn_on_a_piece_in_pieces_toml_is_parsed(tmp_path):
    p = W.default_pieces(4) + [{"id": "HARNESS-x", "owns": ["scripts/x.py"], "status": "landed"}]
    t = spawn(W.default_transcripts(), "hx", "HARNESS-x audit")
    r, got, w = expect(tmp_path, ["M07b"], "FAIL", pieces=p, transcripts=t)
    assert "HARNESS-x" in got["M07b"][1], got["M07b"][1]


# ---- finding 10: lab-phase M10 reads product_lines + lab_lines and skips sum-0 rows
def test_10_lab_M10_uses_product_plus_lab_lines_and_ignores_zero_sum_rows(tmp_path):
    rows = gate(*[{"product_lines": 0, "lab_lines": 100}] * 3, *[{"product_lines": 0, "lab_lines": 0}] * 3)
    r, got, w = expect(tmp_path, ["M10"], "PASS", gate_rows=rows)
    assert re.match(r"METRIC M10 PASS 100(\.0)? vs", got["M10"][1]), got["M10"][1]


def test_10_lab_M10_is_na_when_fewer_than_three_rows_have_lines(tmp_path):
    rows = gate(*[{"product_lines": 0, "lab_lines": 0}] * 3, *[{"product_lines": 0, "lab_lines": 100}] * 2)
    expect(tmp_path, ["M10"], "NA", gate_rows=rows)


# ---- finding 12, DEC-scripts-tests-not-product, DEC-m04-docs-only-week
def _m04_terms(line):
    m = re.search(r"(\d+) docs-only commits, (\d+) product commits", line)
    assert m, line
    return m.groups()


def test_12_scripts_only_and_tests_only_commits_count_in_neither_M04_term(tmp_path):
    a = run(tmp_path / "a", )[1]["M04"][1]
    ex = [({"scripts/foo.py": 5}, W.D["wed"]), ({"tests/specfactory/t.py": 5}, W.D["wed"]),
          ({"scripts/foo.py": 1, "docs/northstar/plans/z.md": 1}, W.D["wed"])]
    b = run(tmp_path / "b", extra_commits=ex)[1]["M04"][1]
    assert _m04_terms(a) == _m04_terms(b), (a, b)


def test_12_a_week_with_docs_only_commits_and_no_product_commit_is_na(tmp_path):
    r, got, w = expect(tmp_path, ["M04"], "NA", prod_commits=0, docs_commits=3)
    assert "docs-only" in got["M04"][1], got["M04"][1]


# ---- finding 13, Q5: M21b counts breach rules only
def test_13_M21b_ignores_context_drift_lines(tmp_path):  # 3 sessions x 34 calls over 400k = 102 `context` lines
    t = W.default_transcripts()
    for i in range(3):
        t[f"sess-ctx{i}.jsonl"] = [W.clean(W.SONNET, W.ts(11, m), ctx=450000) for m in range(34)]
    r, got, w = run(tmp_path, transcripts=t)
    assert re.match(r"METRIC M21b PASS 0 vs", got["M21b"][1]), got["M21b"][1]


# ---- finding 14: any fixtures/ directory under tests/ is excluded
def test_14_M01_ignores_lines_under_tests_specfactory_fixtures(tmp_path):
    expect(tmp_path, ["M01"], "PASS", extra_commits=[({"tests/specfactory/fixtures/big.py": 5000}, W.D["wed"])])


def test_14_M23_ignores_data_under_tests_specfactory_fixtures(tmp_path):
    ex = [({"tests/specfactory/fixtures/golden_x.json": "{}\n", "tests/specfactory/fixtures/d.csv": "a\n"}, W.D["wed"])]
    expect(tmp_path, ["M23"], "PASS", extra_commits=ex)


# ---- finding 15: M11c counts every non-md file outside research/*/data/ and story_reviews/
@pytest.mark.parametrize("ext", ["jsonl", "tsv", "npy", "bin", "yaml", "toml", "log"])
def test_15_M11c_counts_data_extensions_the_allowlist_missed(tmp_path, ext):
    expect(tmp_path, ["M11c"], "FAIL", extra_commits=[({f"docs/northstar/plans/data_x.{ext}": "a\n"}, W.D["wed"])])


def test_15_M11c_does_not_count_a_shot_under_story_reviews(tmp_path):
    expect(tmp_path, ["M11c"], "PASS",
           extra_commits=[({"docs/northstar/story_reviews/westley/shot.png": "png\n"}, W.D["wed"])])


# ---- finding 16: only a file ADDED under a retro folder of the current 14-day window exempts M11 and M24a
OLD_RETRO = {"docs/northstar/plans/retro_2026-09-20/README.md": "old\n"}  # added 2026-10-01, outside the window


def test_16_M11_is_not_na_when_an_old_retro_file_is_modified(tmp_path):
    ex = [({"docs/northstar/plans/big.md": 2000, "docs/northstar/plans/retro_2026-09-20/README.md": ("a", "more\n")}, W.D["wed"])]
    expect(tmp_path, ["M11"], "FAIL", base_files=OLD_RETRO, extra_commits=ex)


def test_16_M11_is_not_na_when_a_file_is_added_into_an_old_retro_folder(tmp_path):
    ex = [({"docs/northstar/plans/big.md": 2000, "docs/northstar/plans/retro_2026-09-20/extra.md": 1}, W.D["wed"])]
    expect(tmp_path, ["M11"], "FAIL", base_files=OLD_RETRO, extra_commits=ex)


def test_16_M24a_is_not_exempt_when_the_commit_only_modifies_an_old_retro_file(tmp_path):
    ex = [({"CLAUDE.md": ("a", f"edit {i}\n"), "docs/northstar/plans/retro_2026-09-20/README.md": ("a", f"m{i}\n")}, W.D["wed"])
          for i in range(5)]
    expect(tmp_path, ["M24a"], "FAIL", base_files=OLD_RETRO, extra_commits=ex)


# ---- findings 17, 32: verdicts by piece id from verdicts_*.md and decisions.md; M17 = rows of the Picture table
def test_17_M16_reads_verdicts_from_the_verdicts_file_by_piece_id(tmp_path):
    p = W.default_pieces(4) + [{"id": "VG-X-c", "owns": ["scenes/x/c.gd"], "status": "attached"}]
    v = "# V\n\n| Picture | Verdict |\n|---|---|\n" + "".join(f"| `VG-X-{x}` | Approved |\n" for x in "abc")
    expect(tmp_path, ["M16"], "PASS", pieces=p, readme_rows=(), verdicts_text=v)


def test_17_M16_reads_verdicts_from_decisions_by_piece_id(tmp_path):
    expect(tmp_path, ["M16"], "PASS", readme_rows=(), verdicts_text="",
           decisions_text="\n| 2026-10-22 | VG-X-a and VG-X-b look pieces approved | x |\n")


def test_17_M16_a_lane_substring_is_not_a_verdict(tmp_path):
    expect(tmp_path, ["M16"], "FAIL", readme_rows=(), verdicts_text="",
           decisions_text="\n| 2026-10-22 | the VG-X lane was discussed | no piece id here |\n")


def test_32_M17_counts_every_row_of_the_picture_table_and_no_other_table(tmp_path):
    r, got, w = run(tmp_path, readme_open=5)  # the README also has a `| Page | ... |` table with one row
    assert got["M17"][0] == "NA" and "5 rows, oldest 12 d" in got["M17"][1], got["M17"][1]


# ---- finding 18
def test_18_M11b_bytes_fails_on_a_19000_byte_claude_md_of_100_lines(tmp_path):
    text = "".join("y" * 189 + "\n" for _ in range(100))
    assert len(text.encode()) == 19000
    r, got, w = expect(tmp_path, ["M11b-bytes"], "FAIL", claude_text=text)
    assert got["M11b"][0] == "PASS", "100 lines is under the line bound; only the bytes are over"


def test_18_control_M11b_bytes_passes_at_17000_bytes(tmp_path):
    text = "".join("y" * 169 + "\n" for _ in range(100))
    assert len(text.encode()) == 17000
    expect(tmp_path, ["M11b-bytes"], "PASS", claude_text=text)


# ---- finding 21: unknown outcomes are a third bucket
def _runs_with_unknown(ok, unknown):
    t = {}
    for i in range(ok):
        spawn(t, f"ok{i}", "P0 build", minute=i % 50)
    for i in range(unknown):
        spawn(t, f"un{i}", "P0 build", result="finished without a result line", minute=i % 50)
    return t


def test_21_M15_prints_the_unknown_count_and_fails_over_20_percent(tmp_path):  # 3 of 11 = 27%
    r, got, w = expect(tmp_path, ["M15"], "FAIL", transcripts=_runs_with_unknown(8, 3), sdk_rows=[])
    assert re.search(r"\b3 unknown\b|unknown[ =:x]*3\b", got["M15"][1]), got["M15"][1]


def test_21_control_M15_passes_at_one_unknown_in_ten(tmp_path):
    r, got, w = expect(tmp_path, ["M15"], "PASS", transcripts=_runs_with_unknown(9, 1), sdk_rows=[])
    assert re.search(r"\b1 unknown\b|unknown[ =:x]*1\b", got["M15"][1]), got["M15"][1]


# ---- finding 22
@pytest.mark.parametrize("phase", ["lab", "beta"])
def test_22_written_json_carries_the_phase(tmp_path, phase):
    r, got, w = run(tmp_path, extra=["--write"], phase=phase)
    j = json.loads((w["repo"] / W.METRICS_DIR / "2026-W44.json").read_text())
    assert j.get("phase") == phase, list(j)


# ---- finding 25: M12c known-bad
def test_25_M12c_fails_in_beta_when_no_story_moved_to_seen(tmp_path):
    expect(tmp_path, ["M12c"], "FAIL", phase="beta", beta_list=BETA_GOOD, stories_seen_in_week=0)


# ---- finding 26: no ledger on origin/main
def test_26_no_ledger_gives_no_rows_and_NA_not_a_traceback(tmp_path):
    r, got, w = run(tmp_path, ledger=False, ledger_week=[])
    assert "Traceback" not in r.stderr, r.stderr[-500:]
    assert got["M03"][0] == "NA" and got["M21a"][0] == "NA", (got.get("M03"), got.get("M21a"))


# ---- finding 33: the detail of a line is capped at 400 characters unless --verbose
def _sixty_fable_sessions():
    return {f"session-{'z' * 20}-{i:03d}.jsonl": [W.entry(W.FABLE, W.ts(10, 3))] for i in range(60)}


def test_33_a_fail_detail_is_at_most_400_characters_without_verbose(tmp_path):
    r, got, w = expect(tmp_path, ["M22"], "FAIL", transcripts=_sixty_fable_sessions())
    assert len(detail(got["M22"][1])) <= 400, len(detail(got["M22"][1]))


def test_33_verbose_prints_the_full_list(tmp_path):
    r, got, w = run(tmp_path, cli=["--verbose"], transcripts=_sixty_fable_sessions())
    assert all(f"{'z' * 20}-{i:03d}" in r.stdout for i in range(60)), "--verbose must list every session"


# ---- the back-test table
def test_24_weeks_prints_a_markdown_table_one_row_per_metric_one_column_per_week(tmp_path):
    w = W.build_world(tmp_path)
    args = [a for a in w["args"]]
    i = args.index("--week")
    del args[i:i + 2]
    r = subprocess.run([sys.executable, str(SCRIPT), *args, "--weeks", "2026-W40..2026-W42"], capture_output=True,
                       text=True, timeout=300)
    assert r.returncode == 0, "the back-test judges nothing, so it exits 0\n" + r.stdout[-600:] + r.stderr[-600:]
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in r.stdout.splitlines() if ln.startswith("|")]
    assert rows, r.stdout + r.stderr
    assert rows[0][1:] == ["2026-W40", "2026-W41", "2026-W42"], rows[0]
    assert all(set(c) <= set("-: ") and "---" in c for c in rows[1]), "second row is the markdown separator, one --- per column"
    body = {x[0]: x for x in rows[2:]}
    assert len(body) == len(rows) - 2, "one row per metric, no repeats"
    assert set(W.TH) <= set(body), sorted(set(W.TH) - set(body))
    assert all(len(x) == 4 and all(x[1:]) for x in body.values()), "one non-empty cell per week"
    assert not [x for x in body.values() if any(c in ("PASS", "FAIL", "DRAFT") for c in x[1:])], "values only"


# ---- Architect ruling 2026-10-27 (e): the stderr note states how many gate rows were skipped
def test_e_malformed_gate_row_note_states_the_skipped_count(tmp_path):
    r, got, w = run(tmp_path, prod_commits=2, gate_rows="auto")
    gp = tmp_path / "gate_runs.csv"
    gp.write_text(gp.read_text() + "2026-10-28,P1,P2,push/p,extra,fields\n")  # fewer fields than the header
    r = subprocess.run([sys.executable, str(SCRIPT), *w["args"]], capture_output=True, text=True, timeout=300)
    assert "skipped 1 malformed gate rows" in r.stderr, r.stderr[-500:]
