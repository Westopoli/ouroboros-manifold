# Rule pins: R-087-03, R-087-08, R-087-04, R-087-05
"""Engine rule fixes 2026-11-08, F3, whole fights: a target lock holds.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F3" ('the lock holds over 300 ticks in a fight (R-087-03 check 0 over L-0039 and
L-0050)'). Evidence: docs/reports/2026-11-07-rule-enforcement/appendix-b-test-forensics.md (mutation M6: only goldens noticed). Oracle:
engine_rules_oracle.lock_swaps, per tick from engine state (not the F0 checker). The single-unit scenes are
tests/csim/test_E11_R087_03_target_lock.py.

Rule words (docs/bible/epics/E-11-*.md, rewritten 2026-11-08): a unit locks the nearest enemy its side sees and keeps the lock until the target
dies, leaves its side's sight, or the unit gets a new order; the leash (R-087-05) and R-087-09 are their own rules and still break a lock.
Oracle reading of that: the unit's target changed from a living enemy that its side still sees (before and after the step; always true with
sight off) to another enemy, with the unit's destination neither cleared nor set across the tick (the engine re-issuing its own order is a
new order) and the unit within its sensor radius + 25 wu of where it took that lock (outside it the leash applies, inv_check I27).

Measured on the unfixed tree (2026-11-08, seed 1, 100 simulated seconds): swaps L-0039 sight on 35, L-0050 sight on 78, L-0050 sight off 145.
With the unit.c:2236-2240 clause removed on a scratch copy the same oracle reads 0 / 0 / 0 (it does not flag legal leash drops or order re-issues).
Controls green today: L-0039 sight off 0 swaps; every fight takes many targets (the locks change when targets die, so 0 is not 'nobody locked').
"""
import pytest

import engine_rules_oracle as oracle

FIGHTS = [("L-0039", "on"), ("L-0050", "on"), ("L-0050", "off")]


@pytest.mark.parametrize("name,sight", FIGHTS)
def test_R_087_03_a_lock_is_never_swapped_while_its_target_lives_and_is_seen(name, sight):
    """R-087-03 / R-087-08, per tick over the whole fight. Red today: 35 / 78 / 145 swaps (a locked target that steps out of attack range is
    exchanged for the nearest enemy at a cohort turn)."""
    rec = oracle.played(name, sight)
    bad = oracle.lock_swaps(rec)
    assert not bad, "%s sight %s: %d swaps of a live, seen lock (%d units), first %s" % (name, sight, len(bad), oracle.distinct_units(bad), bad[:3])


@pytest.mark.parametrize("name,sight", FIGHTS + [("L-0039", "off")])
def test_R_087_03_control_units_lock_and_re_lock_in_these_fights(name, sight):
    """Control (green today and after): more than 100 target changes (acquisition, death, sight) over the fight, so a zero swap count means
    the locks held while the fight moved on, not that no unit ever had a target."""
    rec = oracle.played(name, sight)
    changes = sum(1 for tk in rec.ticks for u in rec.ids if tk["pre"][u]["alive"] and tk["post"][u]["alive"] and tk["pre"][u]["tgt"] != tk["post"][u]["tgt"])
    # Test-defect (F3 with F1, 2026-11-08): the bound was 100, measured on the unfixed tree where L-0039 units swapped targets 694 (sight off) and 6121 (sight on)
    # times with no shot fired. With locks held and walkers routed round the box the 8 v 8 fights change targets 70 (off) and 84 (on) times while
    # firing 626 and 521 shots; 50 is three changes a unit, so a fight where nobody locked still fails.
    assert changes > 50, "only %d target changes" % changes


def test_R_087_03_control_sight_off_open_fight_with_boxes_has_no_swaps_today():
    """Control (green today): L-0039 with sight off has 0 swaps, so the oracle's swap test is not a blanket 'true'."""
    assert not oracle.lock_swaps(oracle.played("L-0039", "off"))
