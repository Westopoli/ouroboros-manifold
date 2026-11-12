# Rule pins: R-087-03, R-096-08, R-087-10
"""Engine rules round 3, T9 item 3: the lab checker (the shipped Monitor, through arena/run.py::fight) reports "not the nearest" for picks the engine may legally make.
The pure predicates are tests/skilllab/test_invariants_nearest.py (the section "Round 3, T9 item 3").

R-087-03 (docs/bible/epics/E-11-units-and-combat.md): "Given an idle or attack-moving unit with no target and an enemy that its side can see ..., When it acquires, Then it targets the nearest such
enemy ...". The engine's own eligibility (guards: R-096-08 "stepping toward it no farther than GUARD_RADIUS = 200 wu from the post"; reach: R-087-10 "the distance is spherical") lets it skip a nearer
enemy it cannot reach from where it may stand; the checker must know that, or every legal pick of that kind is a false report.

Premises dumped 2026-11-11 on this tree (main 7ba38983), run.fight(L-0084, seed 1, sight "on", CAP_SECONDS): 3,718 ticks, 11 reports in all, every one R-087-03; eight of them say "not the nearest
enemy its side sees":
    tick/unit  1083/16 (acquired 78, 499.4 wu, nearest 490.0)   1086/15 (78, 497.3, nearest 481.6)   1556/25 (89, 325.3, nearest 310.1)   1557/26 (89, 336.7, 315.0)
               1558/27 (89, 324.1, 297.8)                        1559/24 (89, 318.1, 314.8)           [guard cases: the nearer enemy was over 500 wu from the post by slant]
               1270/15 (90, 290.8, nearest 285.9)                1271/16 (90, 292.5, 288.6)           [slant cases: the nearer enemy was 327.6 and 330.0 wu away by slant against range 300]
The other three reports of the fight (R-087-03, other wording) are not part of this item and are not asserted here.
Red today: both tests below. Control (green): the fight runs to the measured end and the engine makes these eight picks.

Re-dumped 2026-11-12 on the Round 3 tip (d70c8d47): the fight is 3,923 ticks, side A wins with 37 left; the engine makes the eight picks at the same ticks for the same targets as before; the pre-fix checker
(7ba38983/scripts/skilllab/invariants.py) reports exactly the eight on it, the checker as it is none, and no violation of any rule in all.
"""
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
from scripts.skilllab import invariants  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.arena.snapshot import CAP_SECONDS  # noqa: E402

PAIRS = [(1083, 16), (1086, 15), (1556, 25), (1557, 26), (1558, 27), (1559, 24), (1270, 15), (1271, 16)]
NOT_NEAREST = "not the nearest"


@lru_cache(maxsize=None)
def monitored(name="L-0084", seed=1):
    made, orig = [], invariants.Monitor

    class Cap(orig):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            made.append(self)
    invariants.Monitor = Cap
    try:
        with oracle.recording() as recs:
            frames, last, _, _ = run.fight(oracle.catalogue(name), seed, "on", CAP_SECONDS, 100000)
    finally:
        invariants.Monitor = orig
    made[0].rec, made[0].survivors = oracle.only(recs), frames[last]["alive"]
    return made[0]


def nearest_reports(mon):
    return [(v["tick"], v["unit"], v["detail"]) for v in mon.violations if v["rule"] == "R-087-03" and NOT_NEAREST in v["detail"]]


ACQUIRED = {(1083, 16): 78, (1086, 15): 78, (1556, 25): 89, (1557, 26): 89, (1558, 27): 89, (1559, 24): 89, (1270, 15): 90, (1271, 16): 90}   # from the premise above


def test_control_the_monitor_runs_L0084_to_the_measured_end_and_the_engine_still_makes_the_eight_picks():
    """Control (green before and after the checker fix; re-written 2026-11-12, Test-defect: it asserted the eight false reports, the defect the fix removes). Premise of the tests below: L-0084 seed 1 sight
    on runs 3,923 ticks with nothing suspended (3,718 before Round 3 fix 1, d70c8d47), side A wins with 37 left, and the Monitor judged it (its verdict is True or False, not None as a stand-in's is);
    the engine still makes the eight picks of the premise: at each (tick, unit) the unit takes the target named there (the tick before it held another or none). So the tests below stay about the
    checker: with the pre-fix checker (7ba38983) the same fight still gets the eight 'not the nearest' reports; the checker as it is gets none."""
    mon = monitored()
    assert (mon.tick, mon.suspended, mon.survivors) == (3923, {}, [37, 0])
    assert mon.verdict()["invalid"] is not None
    got = {(n, u): mon.rec.ticks[n - 1]["post"][u]["tgt"] for n, u in ACQUIRED}
    assert got == ACQUIRED and all(mon.rec.ticks[n - 1]["pre"][u]["tgt"] != t for (n, u), t in ACQUIRED.items()), got


def test_R_087_03_the_eight_legal_picks_of_L0084_are_not_reported_as_not_the_nearest():
    """R-087-03 'it targets the nearest such enemy' with the engine's eligibility (R-096-08 post radius for a guard, R-087-10 slant for a unit on another layer): the Monitor reports none of the eight
    (tick, unit) pairs 1083/16, 1086/15, 1556/25, 1557/26, 1558/27, 1559/24, 1270/15, 1271/16 on L-0084 seed 1. Red today: all eight."""
    got = {(t, u) for t, u, _ in nearest_reports(monitored())}
    assert not got & set(PAIRS), sorted(got & set(PAIRS))


def test_R_087_03_the_fight_as_a_whole_reports_no_not_the_nearest_case():
    """R-087-03 (whole run): L-0084 seed 1 sight on has no 'not the nearest enemy its side sees' report at any tick for any unit. Red today: eight reports (the premise list)."""
    got = nearest_reports(monitored())
    assert not got, got
