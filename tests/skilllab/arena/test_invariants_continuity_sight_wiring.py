# Rule pins: R-004-08, R-004-06, R-087-03, R-093-02
"""Engine rules round 2, corrections of 2026-11-11 to the rule checker (`scripts/skilllab/invariants.py`), on real fights. The pure predicates are
tests/skilllab/test_invariants_tightened.py (continuity) and test_invariants_visible.py (suspended_for "off").

1. Continuity is about layer changes, not about every push.
   R-004-08 (docs/bible/epics/E-01-layer-system.md): "... while on the slope the unit counts as being on the layer on its side of the midline, for its own sensing and for what
   may attack it, so a unit that turns back before the midline has not changed layer and one that crosses the midline and comes back has changed twice." (with R-004-06:
   "its transition progress is its position along the slope, not a timer"). The checker's reading (the spec's, not the rule's own words; gap reported): a unit that changes
   layer on a tick does not jump. No rule limits a collision push, so a displacement above max step + slack on a tick with no layer change is excused when another living unit
   is within 40 wu.
   Premises dumped 2026-11-11 on the combined Round 2 branch (ba291db4), the checker as it is (Round 2 PUSH_ALLOWANCE 2.0):
     sixteen Vanguards a side, one blob of radius 60 (formation blob, attack_move), 80 ticks, fight.fight seed 0: 15 continuity violations, all on tick 1, 8 to 19.5 wu
         against a bound of 4.4 + 1.3, every one on layer 0 to 0; eight a side: none.
     L-0061 seed 1 sight on (2234 ticks): continuity 1 (tick 1523, unit 13, 7.7 wu, layer unchanged).
     L-0084 seed 1 sight on (2106 ticks): continuity 2 (tick 884 unit 10, 8.2 wu; tick 915 unit 10, 13.9 wu; layer unchanged).
   The layer-change measure of test_engine_rules_f8_continuity.py is not touched here.

2. A control fight is not judged on sight rules.
   `run.py --control sight` plays each stage 4 fight a second time with targeting by sight OFF (`fight(.., "control", ..)`, the Monitor's sight argument "control"). The runner
   suspends the sight-dependent checks for `--sight off` (`suspended_for("off")`) and not for the control. Premise (seed 1, the whole fight): L-0039 control, 2858 ticks (2730 since the Round 3 chase fix 94da7493, 2026-11-12; the counts below are of the 2858-tick run, the sight rules are suspended on the 2730 one):
   R-087-03 12 violations and R-093-02 2657, the first at tick 14 for units 7 and 15 (they fire at what their side does not see, which a sight-off control does by design);
   L-0039 sight on, 2314 ticks: none of either.
   The pinned rule is the simpler one (both rules suspended, as for `--sight off`): `Rules.suspended` and `Report.suspended` are per rule, so judging the swap half of R-087-03
   while R-087-03 is suspended would be a design change (reported as a gap).
"""
import collections
import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
import engine_rules_r2_probe as probe  # noqa: E402
from scripts.skilllab import fight, invariants  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.arena.snapshot import CAP_SECONDS  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Terrain  # noqa: E402

SWITCH = "OM_TP_TARGET_BY_SIGHT"
SIGHT_RULES = ("R-087-03", "R-093-02")


@lru_cache(maxsize=None)
def played(name, seed, sight):
    """(Monitor, probe Run) of one whole catalogue fight through run.fight; the Monitor is the shipped one (kept whole: document_keys keeps only 20 violations)."""
    made, orig = [], invariants.Monitor

    class Cap(orig):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            made.append(self)
    invariants.Monitor = Cap
    try:
        with probe.probing() as runs:
            run.fight(oracle.catalogue(name), seed, sight, CAP_SECONDS, 100000)
    finally:
        invariants.Monitor = orig
    return made[0], probe.only(runs)


def of(mon, rule):
    return [v for v in mon.violations if v["rule"] == rule]


# ------------------------------------------------------------------ 1. continuity: a dense blob, and hills at ticks with no layer change

def _blob(n):
    def side(s, x):
        return Group(side=s, unit="Vanguard", count=n, formation="blob", x=x, y=1000.0, facing_deg=0.0 if s == 0 else 180.0, layer=0, order="attack_move", params={"radius": 60.0})
    return Setup(groups=(side(0, 1000.0), side(1, 1700.0)), unit_types={}, max_ticks=80, settings={}, terrain=Terrain(canvas=(4000.0, 4000.0)))


def test_R_004_08_control_a_small_blob_through_fight_fight_is_valid():
    """Control (green today): eight Vanguards a side, one blob of radius 60, 80 ticks: fight.fight reports no violation at all, so the harness is sound."""
    r = fight.fight(_blob(8), 0, False)
    assert r.ticks == 80 and (r.violations, r.invalid) == ([], False)


def test_R_004_08_a_dense_blob_of_sixteen_reports_no_continuity_violation():
    """R-004-08 / continuity: sixteen Vanguards a side spawned as one blob push each other apart by 8 to 19 wu on tick 1 (15 violations today, all on layer 0 to 0, each beside
    another unit). A collision push on one layer is no layer change and no rule limits it: no continuity violation, and no other rule is broken either."""
    r = fight.fight(_blob(16), 0, False)
    assert r.ticks == 80
    assert [(v["rule"], v["tick"], v["unit"]) for v in r.violations] == [], r.violations[:3]


@pytest.mark.parametrize("name", ["L-0061", "L-0084"])
def test_R_004_08_control_the_hill_fights_ran_whole_and_change_layers(name):
    """Control (green today): the Monitor and the probe watched the same whole fight of `name` (seed 1, sight on) and units changed layer in it."""
    mon, rec = played(name, 1, "on")
    flips = sum(1 for m in rec.moves if m[3] != m[4])
    assert mon.tick == rec.n > 1000 and flips >= 20, (mon.tick, rec.n, flips)


@pytest.mark.parametrize("name", ["L-0061", "L-0084"])
def test_R_004_08_no_continuity_violation_at_a_tick_without_a_layer_change(name):
    """R-004-08 / continuity: over the whole fight, seed 1, sight on, every continuity violation the Monitor reports is on a tick on which that unit changed layer; one on a
    tick with no layer change is a collision push, which no rule limits. Red today: L-0061 reports 1 (tick 1523, unit 13, 7.7 wu), L-0084 reports 2 (ticks 884 and 915, unit 10,
    8.2 and 13.9 wu), each beside another unit."""
    mon, rec = played(name, 1, "on")
    layers = {(n, u): (l0, l1) for n, u, _, l0, l1, _ in rec.moves}
    same = [(v["tick"], v["unit"]) for v in of(mon, "continuity") if layers[(v["tick"], v["unit"])][0] == layers[(v["tick"], v["unit"])][1]]
    assert same == [], "%s: %d continuity violations on ticks with no layer change, first %s" % (name, len(same), same[:3])


# ------------------------------------------------------------------ 2. the sight-off control is not judged on sight rules

def test_R_093_02_suspended_for_names_both_sight_rules_for_the_control_as_for_off():
    """R-093-02 / R-087-03: `suspended_for("control")` (the Monitor's sight argument for `--control sight`: targeting by sight off) is `suspended_for("off")`, both rules with the
    switch OM_TP_TARGET_BY_SIGHT; "on" suspends neither. (Red today: "control" suspends nothing.)"""
    want = {r: SWITCH for r in SIGHT_RULES}
    assert (invariants.suspended_for("off"), invariants.suspended_for("on")) == (want, {})
    assert invariants.suspended_for("control") == want


def test_R_093_02_control_the_sight_on_run_of_l0039_judges_both_rules_and_breaks_neither():
    """Control (green today): L-0039 seed 1 sight on, the whole fight (2314 ticks): nothing suspended, and no violation of R-087-03 or R-093-02."""
    mon, _ = played("L-0039", 1, "on")
    assert mon.tick == 2314 and mon.suspended == {} and of(mon, "R-087-03") == [] and of(mon, "R-093-02") == []


def test_R_093_02_the_control_run_of_l0039_lists_both_sight_rules_as_suspended():
    """R-093-02 / R-087-03: the control (`fight(.., "control", ..)`, targeting by sight off) of L-0039 seed 1 lists exactly R-087-03 and R-093-02 as suspended with the switch the
    sight-off run uses, in the Monitor and in its verdict. Red today: nothing is suspended."""
    mon, _ = played("L-0039", 1, "control")
    assert mon.suspended == {r: SWITCH for r in SIGHT_RULES} and mon.verdict()["suspended"] == {r: SWITCH for r in SIGHT_RULES}


def test_R_093_02_the_control_run_of_l0039_reports_no_violation_of_either_sight_rule():
    """R-093-02 / R-087-03: with targeting by sight off a unit fires at what its side does not see, by design: the control of L-0039 seed 1 (2730 ticks; 2858 before the Round 3 chase fix 94da7493) reports no violation
    of either rule. Red today: R-087-03 12 and R-093-02 2657, the first at tick 14 for units 7 and 15."""
    mon, _ = played("L-0039", 1, "control")
    got = collections.Counter(v["rule"] for v in mon.violations if v["rule"] in SIGHT_RULES)
    assert mon.tick == 2730 and dict(got) == {}, (dict(got), [(v["rule"], v["tick"], v["unit"]) for v in mon.violations if v["rule"] in SIGHT_RULES][:4])
