# Rule pins: R-087-03, R-096-08, R-087-10
"""Engine rules round 3, T9 item 3: the lab checker (the shipped Monitor, through arena/run.py::fight) reports "not the nearest" for picks the engine may legally make.
The pure predicates are tests/skilllab/test_invariants_nearest.py (the section "Round 3, T9 item 3").

R-087-03 (docs/bible/epics/E-11-units-and-combat.md): "Given an idle or attack-moving unit with no target and an enemy that its side can see ..., When it acquires, Then it targets the nearest such
enemy ...". The engine's own eligibility (guards: R-096-08 "stepping toward it no farther than GUARD_RADIUS = 200 wu from the post"; reach: R-087-10 "the distance is spherical") lets it skip a nearer
enemy it cannot reach from where it may stand; the checker must know that, or every legal pick of that kind is a false report.

Premises (L-0084 seed 1, sight "on", CAP_SECONDS), re-derived 2026-11-18 on the Round 6 tip (Test-defect: R-096-02, the order kept through the pause after the unit's own shot, 66fbc1ee9: first different tick 812, unit 71 keeps its destination;
the fight is 1,987 ticks, survivors [12, 0]; 12 of the 1,955-tick run's 22 picks are in it, 813/34, 1056/13, 1356/51, 79, 84 and 85, 1587/41, 1647/41, 1647/65 and 1707/59 are gone, and 875/40, 1227/78, 1227/82, 1287/51, 1407/41, 1467/59, 1527/65, 1682/35 and 1683/36 are new; the checker still reports no violation of any rule) and
2026-11-17 on the Round 5 fourth-pass tip (Test-defect: the eight picks of the 2026-11-11 dump, ticks 1083 to 1559 and 1270/1271 on the
3,718- and then the 3,923-tick run, are not in the 1,955-tick run: those units hold no target at those ticks). What the eight were there to show is that the engine makes picks a plain "nearest seen
enemy" comparison would call wrong, and that the checker must not report them. In the run as it is, 21 picks (a unit with no living target the tick before takes a target) have, in frame N, a seen
enemy (in the side's visible set in both frames) nearer by more than 1 wu (the checker's NEAREST_TOL) than the target it took; the Monitor, which judges every pick on the readings of the tick's mixed state
(round5.md "Fourth pass"), reports none of them and no violation of any rule on the fight:
    tick/unit  387/60 (31)    387/61 (31)    393/50 (34)    513/53 (34)    517/2 (66)    846/67 (8)     874/39 (68)    875/40 (68)    877/10 (69)   930/73 (32)    1227/78 (31)
               1227/82 (31)   1287/51 (31)   1287/56 (31)   1407/41 (31)   1407/70 (31)  1467/59 (31)   1527/46 (31)   1527/65 (31)   1682/35 (90)  1683/36 (91)
    [the nearer enemy is nearer than the target in frame N by 1.2 to 150.5 wu (1227/78: 482.9 wu to the target against 332.4 to the nearer enemy; 930/73: 448.5 against 340.0; 517/2, 874/39, 875/40, 877/10 and 1683/36: 1 to 4 wu; the
    five narrow ones are guards, units 1 to 40)].
Control (green): the fight runs to the measured end and the engine makes these picks. The function names keep "eight" from the first version of the premise.
"""
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
from scripts.skilllab import invariants  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.arena.snapshot import CAP_SECONDS  # noqa: E402

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


ACQUIRED = {(387, 60): 31, (387, 61): 31, (393, 50): 34, (513, 53): 34, (517, 2): 66, (846, 67): 8, (874, 39): 68, (875, 40): 68, (877, 10): 69, (930, 73): 32, (1227, 78): 31, (1227, 82): 31, (1287, 51): 31, (1287, 56): 31, (1407, 41): 31, (1407, 70): 31, (1467, 59): 31, (1527, 46): 31, (1527, 65): 31, (1682, 35): 90, (1683, 36): 91}   # from the premise above
PAIRS = list(ACQUIRED)


def test_control_the_monitor_runs_L0084_to_the_measured_end_and_the_engine_still_makes_the_eight_picks():
    """Control (green before and after the checker fix; re-written 2026-11-12, Test-defect: it asserted the eight false reports, the defect the fix removes; the picks re-derived 2026-11-17 and 2026-11-18). Premise of the
    tests below: L-0084 seed 1 sight on runs to the measured end with nothing suspended (the length and the survivors re-pinned 2026-11-17 by the verifier, Test-defect: 3923 ticks and [37, 0] were the fight before the notice distance; 1955 and [15, 0]; re-pinned 2026-11-18, Test-defect: 66fbc1ee9, first different tick 812, unit 71, now 1987 and [12, 0]), and the Monitor judged it (its
    verdict is True or False, not None as a stand-in's is); the engine makes the 21 picks of the premise: at each (tick, unit) the unit takes the target named there (the tick before it held another or
    none). So the tests below stay about the checker: a plain frame-N nearest comparison calls each of these picks wrong; the checker as it is reports none."""
    mon = monitored()
    assert (mon.tick, mon.suspended, mon.survivors) == (1987, {}, [12, 0])
    assert mon.verdict()["invalid"] is not None
    got = {(n, u): mon.rec.ticks[n - 1]["post"][u]["tgt"] for n, u in ACQUIRED}
    assert got == ACQUIRED and all(mon.rec.ticks[n - 1]["pre"][u]["tgt"] != t for (n, u), t in ACQUIRED.items()), got


def test_R_087_03_the_eight_legal_picks_of_L0084_are_not_reported_as_not_the_nearest():
    """R-087-03 'it targets the nearest such enemy' with the engine's eligibility (R-096-08 post radius for a guard, R-087-10 slant for a unit on another layer): the Monitor reports none of the 21
    (tick, unit) pairs of the premise (the header lists them) on L-0084 seed 1."""
    got = {(t, u) for t, u, _ in nearest_reports(monitored())}
    assert not got & set(PAIRS), sorted(got & set(PAIRS))


def test_R_087_03_the_fight_as_a_whole_reports_no_not_the_nearest_case():
    """R-087-03 (whole run): L-0084 seed 1 sight on has no 'not the nearest enemy its side sees' report at any tick for any unit."""
    got = nearest_reports(monitored())
    assert not got, got
