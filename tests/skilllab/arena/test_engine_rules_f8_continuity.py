# Rule pins: R-004-06, R-004-08, R-190-04
"""Engine rule fixes 2026-11-08, F8, whole fights: a unit that changes layer on a hill does not jump.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F8" and "Round 2 acceptance". Evidence: appendix-c-invariant-sweep.md I5tL (951 jumps of 24 to 78 wu with a layer change,
13 of 14 hill layouts) and I23 (31,839 flickers). The single-walker and crowd scenes are tests/csim/test_E01_R004_layer_change_is_continuous.py. The probe is
engine_rules_r2_probe.py (per tick, from engine state, no push excuse).

Rule words (docs/bible/epics/E-01-layer-system.md, as written 2026-11-08): R-004-06 'its transition progress is its position along the slope ... below the midline, units
on layer L may attack it ... at or above the midline, units on layer L+1 may' and R-004-08 'a unit that turns back before the midline has not changed layer and one that
crosses the midline and comes back has changed twice'. The rules let the LAYER flip (twice at a midline); they do not say in words that the position is continuous: that is the
spec's reading (gap reported). Bound: every living unit moves at most speed x max(1, OM_TP_SLOPE_DOWN_MULT) / 20 + DRAFT-inv-step-slack 1.3 wu a tick, on a layer-change tick too.

Measured on the Round 1 tip (94c2fb5d, seed 1, sight on, each fight to its end), unit-ticks that change layer and move more than the bound, NO push excuse:
  L-0061 574 of 2552 layer changes (worst 78.1 wu, a 4.4 wu/tick Vanguard)   L-0063 1788 of 3407 (worst 92.0)   L-0080 276 of 548 (worst 30.6)   L-0083 14 of 27 (the fight has 338 unit-ticks over the
  bound in all, worst 75.4 wu)   L-0084 1596 of 2473 (measured 2026-11-11 on the same tip, seed 1, sight on)
  the F0 checker's `continuity` over the same four fights: 0, 0, 0, 0. It excuses every unit that has another unit within 40 wu before or after the tick (_pushed), and a
  hill march is dense. On an open field (L-0050, 24 walkers, 103,000 unit-ticks) no unit-tick exceeds the bound by more than 2 wu, so a push is not what moves a unit 78 wu.
The checker's blind spot is reported as a gap; these tests are the proof, the checker test below is the control the brief asked for.

L-0080 replaced by L-0084 (2026-11-11, Test-defect: the control below required 20 layer changes of L-0080, a fight that no longer has them). Layer-change unit-ticks
(a unit whose layer differs before and after the step), seed 1, sight on, each fight to its end, measured on the Round 2 tree `2c38b0aa` / on the Round 1 tip 94c2fb5d:
  L-0061 3933 (24 units) / 2552     L-0063 9380 (48 units) / 3407     L-0083 25 (17 units) / 27     L-0080 7 (7 units, 12000 ticks) / 548     L-0084 7142 (53 units) / 2473
L-0080 fell from 548 to 7 (the Round 2 fixes: per the brief, units on its hill now hold and shoot down instead of walking; not traced here); its jump test still judges 7 changes,
too few to call the fight a ramp crossed by many units. L-0084 is the catalogue's `slope` layout (40:56, hold:A, small_tiered): the whole defence is spread over a ramp,
53 of its 96 units change layer, and the jump test over it is red on the Round 1 tip (1596 unit-ticks over the bound) and green on Round 2 (0). Candidates measured
on Round 2 (layer-change unit-ticks): L-0062 9353, L-0064 993, L-0065 3161, L-0066 5903, L-0079 77, L-0081 8, L-0082 260, L-0084 7142; the flank_route layouts
L-0067, L-0069 and L-0071 have none.
"""
import collections
import tomllib

import pytest

import engine_rules_oracle as oracle
import engine_rules_r2_probe as probe

HILLS = ["L-0061", "L-0063", "L-0083", "L-0084"]
SLACK = probe.STEP_SLACK
_CACHE = {}


def _fight(name):
    """One sight-on fight of the layout through the arena runner, probed, and the F0 Monitor's full violation list kept (document_keys keeps only 20)."""
    if name in _CACHE:
        return _CACHE[name]
    from scripts.skilllab import invariants
    from scripts.skilllab.arena import run
    stash = {}
    orig = invariants.Monitor.document_keys

    def keys(self):
        stash["v"] = list(self.violations)
        return orig(self)

    invariants.Monitor.document_keys = keys
    try:
        with probe.probing() as runs:
            run.fight(oracle.catalogue(name), 1, "on", 600, 100000)
    finally:
        invariants.Monitor.document_keys = orig
    _CACHE[name] = (probe.only(runs), stash["v"])
    return _CACHE[name]


def _jumps(run, only_layer_change):
    return [(n, u, round(d, 1), round(top, 2), l0, l1) for n, u, d, l0, l1, top in run.moves
            if d > top + SLACK and (l0 != l1 or not only_layer_change)]


@pytest.mark.parametrize("name", HILLS)
def test_R_004_08_control_the_fights_change_layer_many_times(name):
    """Control (green today and after): each hill fight has at least 20 unit-ticks on which a unit changes layer, so the rule below is tested on real layer changes."""
    run, _ = _fight(name)
    flips = sum(1 for m in run.moves if m[3] != m[4])
    assert flips >= 20, "%s: only %d layer changes in %d ticks" % (name, flips, run.n)


@pytest.mark.parametrize("name", HILLS)
def test_R_004_06_the_checkers_continuity_check_reports_zero(name):
    """The brief's check: the F0 checker's own `continuity` reports zero over the whole fight. GREEN TODAY (0, 0, 0, 0) and a control, not a proof: the check excuses any unit
    with a neighbour within 40 wu (see the module docstring), which hides the jumps the next test counts."""
    _, violations = _fight(name)
    count = collections.Counter(v["rule"] for v in violations)["continuity"]
    assert count == 0, "%s: the checker reports %d continuity violations" % (name, count)


@pytest.mark.parametrize("name", HILLS)
def test_R_004_08_no_unit_jumps_on_the_tick_it_changes_layer(name):
    """R-004-06 / R-004-08 (the spec's reading: the layer flips, the position does not jump), every tick of the whole fight, no push excuse: a unit that changes layer on a
    tick moves at most its top step + 1.3 wu that tick. Red on the Round 1 tip: 574 / 1788 / 14 / 1596 unit-ticks over the bound for L-0061 / L-0063 / L-0083 / L-0084 (worst 78 wu)."""
    run, _ = _fight(name)
    bad = _jumps(run, only_layer_change=True)
    assert not bad, "%s: %d layer-change unit-ticks over speed x max(1, down mult) / 20 + %.1f (%d units), first (tick, unit, wu, top step, layer from, to) %s" % (
        name, len(bad), SLACK, len({b[1] for b in bad}), bad[:3])


def test_R_004_08_control_an_open_field_has_no_unit_over_the_bound():
    """Control (green today and after): L-0050 (no features, no layers, 24 walkers a side, sight on) has no unit-tick over the bound by more than the slack, so the bound
    and the probe are not a blanket 'true', and a push alone never exceeds it. (One unit-tick of 103,000 measured 0.7 over the bound's 1.3: a tolerance of 2 wu is allowed here.)"""
    run, _ = _fight("L-0050")
    bad = [(n, u, round(d, 1)) for n, u, d, l0, l1, top in run.moves if d > top + 2.0]
    assert len(run.moves) > 10000 and not bad, "L-0050: %d unit-ticks over the bound + 2.0 of %d: %s" % (len(bad), len(run.moves), bad[:3])
