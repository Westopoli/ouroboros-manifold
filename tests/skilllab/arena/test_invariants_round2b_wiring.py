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

Re-dumped 2026-11-12 on the Round 3 tip (d70c8d47): fights 2136 / 3923 / 847 ticks, no violation of any rule in any (the cover fixture is 801 ticks on the Round 4 tip 6d3d7635, R-097-10, still none; first different tick 575). The L-0061 tick 42, L-0084 tick 349 and cover tick 206 events still happen (the unit
changes target there). The L-0084 tick 1754 lag (guards 33, 39 and 40 holding 93 for one tick after the sight check) is gone: they now drop at tick 1754 (Round 3 fix 1), and unit 13 of the cover fixture
no longer gives enemy 6 up at tick 376 (it holds it past tick 420): the two tests for those two events (R-093-02 L-0084, R-087-09 tick 376) pass without meeting the case, which the pure tests
(tests/skilllab/test_invariants_visible.py, test_invariants_give_up.py) still cover.
"""
import sys
from functools import lru_cache
from pathlib import Path

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
    """Control (green today and after, unless the engine changes): L-0061 seed 1 1415 ticks, L-0084 seed 1 1987, the cover fixture 957; sight on suspends nothing. Proves the fights below are the
    ones the premises were dumped on. Re-dumped 2026-11-12 on the Round 3 tip (d70c8d47; Test-defect: dumped before the Round 3 engine fixes): was 2234 / 3718 / 1086 on 7ba38983. L-0061: 2234 -> 2025
    at fix 3 (8f825d59) -> 2136 at fix 2 (94da7493); L-0084: 3718 -> 3923 at fix 1 (d70c8d47); cover: 1086 -> 847 at fix 2 -> 801 on the Round 4 tip 6d3d7635 (R-097-10: an idle unit steps aside for a mover of its own side; first different tick 575; Test-defect: dumped
    before it). Re-pinned 2026-11-17 on the Round 5 fourth-pass tip (Test-defect: the lengths were the fights before the notice distance of R-087-04): 2136 -> 1415, 3923 -> 1955, 801 -> 957; the lab checker
    reports no violation of any rule on any of the three. Re-pinned 2026-11-18 on the Round 6 tip (Test-defect: R-096-02, an order kept through the pause after the unit's own shot, 66fbc1ee9; L-0084 first different tick 812, unit 71 keeps its destination): 1955 -> 1987; L-0061 and the cover fixture keep their lengths, none reports a violation."""
    got = [(played(n)[0].tick, played(n)[0].suspended) for n in ("L-0061", "L-0084", "cover")]
    assert got == [(1415, {}), (1987, {}), (957, {})]


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


def test_R_087_04_premise_unit_13_holds_enemy_4_and_closes_on_it_in_the_cover_fixture():
    """Premise of the test below (green; re-derived 2026-11-18 on the Round 6 tip, Test-defect: R-096-02, an order kept through the pause after the unit's own shot, 66fbc1ee9, moved the cover fixture at tick 378, unit 15; the pair
    it pinned, unit 13 taking enemy 4 at tick 636 at 320.54 wu, is not in the fight: unit 13 takes the same enemy 4 at tick 628, 327.01 wu away): on the cover fixture now unit 13
    (range 300) takes enemy 4 at tick 628 (cohort turn; it held none on ticks 625 to 627), 327.01 wu away, outside its range and inside its notice distance 330, holds it on every tick 628 to 643 with its attack-move destination, walks
    to 301.13 wu by tick 642 (the last tick outside range, about 1.8 wu a tick), is inside range at 299.46 wu at tick 643 and stands at 298.47 wu from tick 646. (Earlier on the Round 5 tip: tick 636, 320.54 wu, inside range at tick 646,
    standing at 297.59 wu from tick 649.)"""
    _, rec = played("cover")
    u, t = 13, 4
    rng = rec.stats[rec.typ[u]]["attack_range"]
    assert rng == 300.0
    assert [rec.ticks[n - 1]["post"][u]["tgt"] for n in (627, 628)] == [0, t]
    rows = [tk for tk in rec.ticks if 628 <= tk["n"] <= 643]
    assert len(rows) == 16
    dist = {}
    for tk in rows:
        q = tk["post"][u]
        dist[tk["n"]] = ((q["x"] - tk["post"][t]["x"]) ** 2 + (q["y"] - tk["post"][t]["y"]) ** 2) ** 0.5
        assert q["tgt"] == t and q["dest"] is not None, (tk["n"], q["tgt"], dist[tk["n"]], q["dest"])
    assert abs(dist[628] - 327.01) < 0.5 and abs(dist[643] - 299.46) < 0.5, (dist[628], dist[643])
    assert dist[628] > rng and all(dist[n] > rng for n in range(628, 643)), dist     # outside attack range until tick 643: the case 'a held target just outside attack range'


def test_R_087_04_finding_a_unit_holding_a_target_just_outside_attack_range_walks_toward_it():
    """R-087-04 (E-11): "... acquires the nearest such enemy at its cohort turn (R-087-08), anchors where it stands (R-087-05) and walks toward it until the enemy is within attack range, then
    halts and fires". Written to the rule text: unit 13 of the cover fixture holds enemy 4, 327.01 wu away with range 300, from tick 628; by tick 638 it must be closer than at tick 629 by more
    than 1 wu. Re-pinned 2026-11-18 (Test-defect: Round 6, 66fbc1ee9; the same pair, picked at tick 628 at 327.01 wu, 629 and 638 for 637 and 646; see the premise test above), and 2026-11-17 (Test-defect: the pair was unit 13 and enemy 6, ticks 357 and 375, from the fight before Round 3 fix 2 and Round 5; see the premise test above). The assertion is unchanged.
    The case itself is tests/csim/test_E11_R087_04_chase_resumes_after_the_pause.py. Reported, not asserted: the same fixture has unit 13 (ticks 264 to 433, enemy 2) and unit 10 (265 to 433), standing
    still 322 wu from a held enemy, with a destination, for 170 ticks."""
    _, rec = played("cover")
    u, t = 13, 4
    def dist(n):
        tk = rec.ticks[n - 1]
        q, r = tk["post"][u], tk["post"][t]
        return ((q["x"] - r["x"]) ** 2 + (q["y"] - r["y"]) ** 2) ** 0.5
    assert dist(638) < dist(629) - 1.0, "distance %.2f at tick 629, %.2f at tick 638: the unit stood still" % (dist(629), dist(638))
