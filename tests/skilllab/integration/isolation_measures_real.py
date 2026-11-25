# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md, piece LI2 (the isolation measures), whole-run checks on real recorded fights
"""Helpers shared by test_isolation_measures_real_*.py. The module under test is imported lazily so a missing module fails each test (red), not the collection.

Real fights, read-only, recorded by the R6 comparison (`engine-rules-baseline/r6-compare`, seed 1, a frame every 2 ticks, one attack-move click per side, sight off):
SIT-0106 is the stage 3 situation (L-9106 / L-0106 file ids, 24 a side v 48, hold_and_attack, attacker B); L-0054 is the 128 v 128 meeting (both_same_point).
Versions: approved = engine at 4fa618ce7 (stage 3 approval); today = main 45245ff88; A = the old side-step rule (variant A, branch s/movement-sidestep).
`facts` = r6-compare/out/<fight>-<version>.facts.json, computed by r6-compare/tmp/stats.py (never fired, idle at the end, overlap pairs): the measures must reproduce them.

Premises dumped 2026-11-24 from these files: schema om-fight-2; `orders` {mode, attacker, point} and `ranges` {Vanguard: 300 (+ Bombard, Warden in SIT)} present, `sights` absent (sight off);
every unit row has `fired` and `target`; the ladder files are one line of JSON with the header (result, orders, ranges) before `frames`; the r6-compare/runs/A-* files are indented, keys sorted,
`frames` FIRST and the header AFTER it; the L-0054 files are 150 to 230 MB, so a reader streams frames and never holds them all."""
import json
import re
from pathlib import Path
from types import SimpleNamespace

BASE = Path("/home/westopoli/Projects/om-wt/engine-rules-baseline")
LADDER = BASE / "r6-ladder" / "out"
CMP = BASE / "r6-compare"
OUT = CMP / "out"


def m():
    import importlib
    return importlib.import_module("scripts.skilllab.arena.isolation_measures")


def _case(fight, version, path, facts, winner, survivors, last_tick, mode):
    return SimpleNamespace(key="%s-%s" % (fight, version), fight=fight, version=version, path=path, facts_path=OUT / ("%s-%s.facts.json" % (fight, facts)),
                           winner=winner, survivors=survivors, last_tick=last_tick, mode=mode)


# the known results (brief, 2026-11-24): SIT-0106 approved 11:0 tick 2315, today 5:0 tick 2543, A 0:13 tick 2301; L-0054 approved 9:0 tick 8954, today 14:22 tick 10860, A 0:17 tick 6408
SIT = [
    _case("SIT-0106", "approved", LADDER / "L-9106-s1.4fa618ce7.every2ticks.fight.json", "approved", "A", [11, 0], 2315, "hold_and_attack"),
    _case("SIT-0106", "today", LADDER / "L-9106-s1.45245ff88.every2ticks.fight.json", "today", "A", [5, 0], 2543, "hold_and_attack"),
    _case("SIT-0106", "A", CMP / "runs" / "A-sit" / "L-0106-s1-every2.fight.json", "A", "B", [0, 13], 2301, "hold_and_attack"),
]
L54 = [
    _case("L-0054", "approved", LADDER / "L-0054-s1.4fa618ce7.every2ticks.fight.json", "approved", "A", [9, 0], 8954, "both_same_point"),
    _case("L-0054", "today", LADDER / "L-0054-s1.45245ff88.every2ticks.fight.json", "today", "draw", [14, 22], 10860, "both_same_point"),
    _case("L-0054", "A", CMP / "runs" / "A-l54" / "L-0054-s1-every2.fight.json", "A", "B", [0, 17], 6408, "both_same_point"),
]


def facts(case):
    return json.loads(case.facts_path.read_text())


def header_result(path):
    """The `result` object of a fight file, found in the first 8000 bytes (ladder files) or the last 4000 (indented files, header after frames); never the whole file."""
    size = path.stat().st_size
    with open(path, "rb") as fh:
        head = fh.read(8000).decode("utf-8", "replace")
        fh.seek(max(0, size - 4000))
        tail = fh.read().decode("utf-8", "replace")
    for blob in (head, tail):
        hit = re.search(r'"result":\s*(\{[^{}]*\})', blob)
        if hit:
            return json.loads(hit.group(1)), head
    raise AssertionError("no result object in the head or tail of %s" % path)


def control_real_file(case):
    """Green today: the file exists and its own result is the known one and the facts file's."""
    assert case.path.is_file(), case.path
    res, head = header_result(case.path)
    f = facts(case)
    assert (res["winner"], res["survivors"], res["ticks"]) == (case.winner, case.survivors, case.last_tick)
    assert (f["winner"], f["survivors_A_B"], f["last_tick"]) == (case.winner, case.survivors, case.last_tick)
    return head


_memo = {}


def measured(case):
    """(doc, row): the document opened with the module's loader and `measure_fight` run once per case per process."""
    if case.key not in _memo:
        mod = m()
        doc = mod.load_fight(case.path)
        _memo[case.key] = (doc, mod.measure_fight(doc, spread_ticks=[0, 1000]))
    return _memo[case.key]


def assert_reproduces_facts(case):
    """The whole-run claims. Where a measure's definition differs from the facts' (stats.py) it is said here:
    - idle_units: same definition as stats.py `idle200_at_end` (alive, still, no target, run of 200+ ticks ending at the last frame; arrived < 75 wu of orders.point; behind = a living friend within 40 wu nearer
      the point), so it reproduces total, arrived, behind and front exactly. Holders count as idle in both (the facts do not separate them).
    - orders_ended_short: DIFFERS from the facts: it counts only units that were ordered (hold_and_attack: the attacker's side), not arrived, and with no enemy in notice, at their last living frame, so units that died
      are listed apart. With stuck_ticks equal to the idle duration, `alive_at_end` equals idle total minus arrived on these files (none of them has an idle unit with an enemy in weapon range or a holder
      with an idle run, except where noted below).
    - never_fired and overlap: the facts' definitions (`fired` true in no frame; look rig check_overlap radius 15, max 3 frames), reproduced exactly."""
    mod = m()
    doc, row = measured(case)
    f = facts(case)
    # result and survivors
    assert row["result"]["winner"] == case.winner
    assert row["result"]["last_tick"] == case.last_tick
    assert row["survivors"] == case.survivors == f["survivors_A_B"]
    assert row["margin_survivors"] == case.survivors[0] - case.survivors[1]
    assert row["result"]["defect"] is (case.winner == "draw")
    # strength share: the winner's side ahead, within [-1, 1] and never more than its survivors share
    ms = row["margin_hp_share"]
    assert -1.0 <= ms <= 1.0
    if case.winner == "A":
        assert 0.0 < ms
    if case.winner == "B":
        assert ms < 0.0
    # never fired
    assert row["never_fired"] == f["never_fired"]
    # idle units
    idle = f["idle200_at_end"]
    assert {k: row["idle_units"][k] for k in ("total", "arrived", "behind", "front")} == {k: idle[k] for k in ("total", "arrived", "behind", "front")}
    # orders ended short (see docstring)
    short = mod.orders_ended_short(doc, stuck_ticks=mod.DRAFT_IDLE_TICKS_200)
    assert short["basis"].startswith("fallback")
    if case.mode == "both_same_point":
        assert len(short["alive_at_end"]) == idle["total"] - idle["arrived"]
    else:
        assert len(short["alive_at_end"]) <= idle["total"] - idle["arrived"]
    assert {u["id"] for u in short["alive_at_end"]}.isdisjoint({u["id"] for u in short["died"]})
    assert {u["id"] for u in short["alive_at_end"]} <= {u["id"] for u in row["idle_units"]["units"]}
    assert all(u["since"] <= u["tick"] for u in short["alive_at_end"] + short["died"])
    # overlap pairs, as the look rig reports them
    ov = f["overlap_radius15_max3"]
    assert row["overlap"]["verdict"] == ov["verdict"]
    assert row["overlap"]["pairs"] == ov["detail"]
    assert (row["overlap"]["radius"], row["overlap"]["max_ticks"]) == (ov["radius"], ov["max_ticks"])
    assert row["overlap"]["total_pair_frames"] >= sum(p["ticks"] for p in ov["detail"])
    assert row["overlap"]["max_per_frame"] >= (1 if ov["detail"] else 0)
    # units firing
    uf = row["units_firing"]
    by = uf["by_frame"]
    assert len(by) == f["frames"] and by[0][0] == 0 and by[-1][0] == f["last_frame_tick"]
    assert all(b[0] > a[0] for a, b in zip(by, by[1:]))
    c = uf["first_contact"]
    assert c is not None and row["first_contact_tick"] == c
    assert all(b[1] + b[2] == 0 for b in by if b[0] < c) and any(b[1] + b[2] > 0 for b in by if b[0] == c)
    rate = doc["tick_rate"]
    whole = [sum(b[1 + s] * (b[0] - a[0]) for a, b in zip(by, by[1:])) / rate for s in (0, 1)]
    win = [sum(b[1 + s] * (b[0] - a[0]) for a, b in zip(by, by[1:]) if c <= b[0] < c + 40) / rate for s in (0, 1)]
    assert uf["whole"] == pytest_approx(whole) and uf["window"] == pytest_approx(win)
    assert uf["peak"] == [max(b[1] for b in by), max(b[2] for b in by)]
    # predictions and agreement
    p = row["predictions"]
    assert p["agreement"] == mod.agreement_word(row["result"]["winner"], p["count"], p["type"])
    assert p["count"] == ("A" if uf["window"][0] > uf["window"][1] else "B" if uf["window"][1] > uf["window"][0] else "tie")
    assert p["agreement"] in ("both_right", "count_wrong_type_right", "count_right_type_wrong", "both_wrong", "n/a")
    if case.winner == "draw":
        assert p["agreement"] == "n/a"
    # spread at tick 0 and 1000
    sp = row["spread"]
    assert set(sp) == {0, 1000}
    assert all(isinstance(sp[0][s], float) and sp[0][s] > 0.0 for s in "AB")


def pytest_approx(values):
    import pytest
    return pytest.approx(values, rel=1e-9, abs=1e-9)
