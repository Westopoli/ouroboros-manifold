# Rule pins: R-087-03, R-087-04, R-087-09, R-093-02, R-096-08
"""Engine rules round 2, T8: four places where the lab's checker (the shipped Monitor, through arena/run.py::fight) reports a legal behaviour, on the real fights an engine tracer measured.
The pure predicates are tests/skilllab/test_invariants_give_up.py, _nearest.py and _visible.py.

Premises dumped 2026-11-11 on this tree (combined Round 2 branch d5be5d7d, the checker as it is), sight on, run.fight(.., sight "on", CAP_SECONDS):
  L-0061 seed 1      2234 ticks, one report: R-087-03 tick 42 unit 19 "target 28 -> 26 while 28 was alive and seen" (a guard dropping a target 496.40 wu from its post, 500.01 by slant).
  L-0084 seed 1      3718 ticks: R-087-03 82 reports (the first: tick 349 unit 14 "target 62 -> 64 ..."), R-093-02 3 reports, all at tick 1754 (units 33, 39, 40 "holds 93, which its side did not see
                     before the step"). Seed 10 gives the same list.
  COVER (the h088 cover fixture of tests/skilllab/arena/test_closeup.py with side A Raiders, hold:A; seed 1) 1086 ticks: R-087-03 9 reports: tick 206 unit 15 (acquired 3 at 236.2 wu, the
                     nearest being the given-up 4 at 232.7), ticks 355 unit 12, 356 unit 13, 366 unit 15 (acquired 6, farther than another enemy), tick 376 unit 13 and tick 395 unit 16
                     ("target 6 -> 5"), ticks 762 unit 15, 764 unit 13, 771 unit 16 (acquired 8 at 193.4, 235.0 and 246.3 wu against 184.3, 231.2 and 238.9). Only the named ones are pinned
                     here; the others are reported to the Architect, not asserted.
  Unit 13 of the cover fixture (a type-2 walker, attack range 300, sensor 700, speed 80): target 0 at ticks 354 and 355, takes enemy 6 at tick 356 (cohort turn) at 301.3 wu, holds it
                     through tick 375 standing at (2123.2, 1861.9) with no destination, moved 0.00 wu a tick, fires nothing; at tick 376 it takes enemy 5 and gets a destination. R-087-04 (E-11):
                     "walks toward it until the enemy is within attack range, then halts and fires".
"""
import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
import h088_fixtures as f8  # noqa: E402
from scripts.skilllab import invariants  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.arena.snapshot import CAP_SECONDS  # noqa: E402


@lru_cache(maxsize=None)
def played(name, seed=1):
    """(monitor, recorder) of one whole fight through run.fight: a catalogue layout `name`, or "cover" for the h088 cover fixture with side A Raiders (as test_closeup.py builds it)."""
    if name == "cover":
        lay = f8.cover_layout("L-9921")
        for u in lay["side_a"]["units"]:
            u["role"] = "Raider"
    else:
        lay = oracle.catalogue(name)
    made, orig = [], invariants.Monitor

    class Cap(orig):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            made.append(self)
    invariants.Monitor = Cap
    try:
        with oracle.recording() as recs:
            run.fight(lay, seed, "on", CAP_SECONDS, 100000)
    finally:
        invariants.Monitor = orig
    return made[0], oracle.only(recs)


def at(mon, rule, tick, unit=None):
    return [v for v in mon.violations if v["rule"] == rule and v["tick"] == tick and (unit is None or v["unit"] == unit)]


def test_control_the_monitor_runs_the_three_fights_to_the_measured_ends():
    """Control (green today and after, unless the engine changes): L-0061 seed 1 2234 ticks, L-0084 seed 1 3718, the cover fixture 1086; sight on suspends nothing. Proves the fights below are the
    ones the premises were dumped on."""
    got = [(played(n)[0].tick, played(n)[0].suspended) for n in ("L-0061", "L-0084", "cover")]
    assert got == [(2234, {}), (3718, {}), (1086, {})]


def test_R_096_08_a_guard_dropping_a_target_beyond_radius_plus_range_by_slant_is_not_an_r_087_03_report_L0061():
    """R-096-08 / R-087-03 'the target is a lock': L-0061 seed 1 has no R-087-03 report at tick 42 (unit 19, a guard, drops a target at 500.01 wu by slant against a limit of 500). Red today."""
    mon, _ = played("L-0061")
    assert at(mon, "R-087-03", 42) == [], at(mon, "R-087-03", 42)


def test_R_096_08_a_guard_dropping_a_target_beyond_radius_plus_range_by_slant_is_not_an_r_087_03_report_L0084():
    """R-096-08 / R-087-03: L-0084 seed 1 has no R-087-03 report at tick 349 for unit 14 (a guard drops a target 526.85 wu from its post horizontally, 550.6 by slant, limit 550). Red today."""
    mon, _ = played("L-0084")
    assert at(mon, "R-087-03", 349, 14) == [], at(mon, "R-087-03", 349, 14)


def test_R_087_09_the_nearest_pick_after_a_give_up_is_not_an_r_087_03_report():
    """R-087-03 with R-087-09: the cover fixture has no R-087-03 report at tick 206 for unit 15 (it gave up enemy 4 at tick 205 and took enemy 3, 236.2 wu, the nearest other enemy; the given-up
    4 stood 232.7 wu away). Red today."""
    mon, _ = played("cover")
    assert at(mon, "R-087-03", 206, 15) == [], at(mon, "R-087-03", 206, 15)


def test_R_087_09_a_give_up_of_a_target_just_outside_attack_range_is_not_an_r_087_03_report():
    """R-087-09 as the engine counts it: the cover fixture has no R-087-03 report at tick 376 for unit 13 (it held enemy 6 at 301.3 wu, range 300, standing still with no route for 20 ticks, and
    the engine dropped it at tick 376). Red today."""
    mon, _ = played("cover")
    assert at(mon, "R-087-03", 376, 13) == [], at(mon, "R-087-03", 376, 13)


def test_R_093_02_one_tick_of_lag_on_sight_is_not_a_report_L0084():
    """R-093-02 with the engine's one-tick lag: L-0084 seed 1 has no R-093-02 report (the three it has today are all at tick 1754, units 33, 39 and 40, holding 93 for the single tick between
    the engine's sight check and its drop). Red today."""
    mon, _ = played("L-0084")
    got = [(v["tick"], v["unit"]) for v in mon.violations if v["rule"] == "R-093-02"]
    assert got == [], got


def test_R_087_04_premise_unit_13_holds_an_out_of_range_target_standing_still_in_the_cover_fixture():
    """Premise of the finding below (green today; pinned from the engine tracer, tick by tick): unit 13 of the cover fixture holds enemy 6 on ticks 356 to 375, 301.3 wu away with attack range
    300, with no destination, its position unchanged (moved under 0.5 wu a tick), and fires nothing."""
    _, rec = played("cover")
    u, t = 13, 6
    rng = rec.stats[rec.typ[u]]["attack_range"]
    assert rng == 300.0
    rows = [tk for tk in rec.ticks if 356 <= tk["n"] <= 375]
    assert len(rows) == 20
    for tk in rows:
        p, q = tk["pre"][u], tk["post"][u]
        d = ((q["x"] - tk["post"][t]["x"]) ** 2 + (q["y"] - tk["post"][t]["y"]) ** 2) ** 0.5
        moved = ((q["x"] - p["x"]) ** 2 + (q["y"] - p["y"]) ** 2) ** 0.5
        assert q["tgt"] == t and rng < d <= rng + 2.0 and q["dest"] is None and moved < 0.5 and not [f for f in tk["fires"] if f[0] == u], (tk["n"], q["tgt"], d, q["dest"], moved)


@pytest.mark.xfail(strict=True, reason="FINDING, not for the checker's implementer (engine, needs an engine trace): R-087-04 says a unit that holds a target outside attack range 'walks toward it until the enemy "
                   "is within attack range'; the engine's unit 13 stands still for 20 ticks 1.3 wu out of range and then gives the target up. Strict, so a change in the engine or the rule shows up.")
def test_R_087_04_finding_a_unit_holding_a_target_just_outside_attack_range_walks_toward_it():
    """R-087-04 (E-11): "... acquires the nearest such enemy at its cohort turn (R-087-08), anchors where it stands (R-087-05) and walks toward it until the enemy is within attack range, then
    halts and fires". Written to the rule text: unit 13 of the cover fixture holds enemy 6, 301.3 wu away with range 300, from tick 356; by tick 375 it must be closer than at tick 357 by more
    than 1 wu. Measured: the distance is 301.3 on every one of those ticks (the unit does not move), see the premise test above. The engine, not the checker, is what differs; the cause
    (no route is built for an out-of-range target whose line is blocked?) needs an engine trace and is not asserted here. Red today."""
    _, rec = played("cover")
    u, t = 13, 6
    def dist(n):
        tk = rec.ticks[n - 1]
        q, r = tk["post"][u], tk["post"][t]
        return ((q["x"] - r["x"]) ** 2 + (q["y"] - r["y"]) ** 2) ** 0.5
    assert dist(375) < dist(357) - 1.0, "distance %.2f at tick 357, %.2f at tick 375: the unit stood still" % (dist(357), dist(375))
