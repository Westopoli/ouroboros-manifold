# Rule pins: R-083-03, R-084-01
"""Engine rule fixes 2026-11-08, F4, whole fights: Wardens do not stack.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F4"; Q-084-01 closed 'no stacking' 2026-10-20. Evidence:
docs/reports/2026-11-07-rule-enforcement.md (sweep I10s). Oracle: engine_rules_oracle.warden_overheal (a unit's hp rose by more than one
Warden's 0.075 in a tick on which nothing hit it), per tick from engine state, not the F0 checker. The exact arithmetic (heal and
reduction for 1, 2, 3 Wardens) is tests/csim/test_E11_R083_03_wardens_do_not_stack.py.

Rule words: R-083-03 'a second Warden adds nothing' (heal 0.075 hp a tick once); R-084-01 the Warden aura reduction is 0.10, once.

Measured on the unfixed tree (2026-11-08, seed 1, 100 simulated seconds): unit-ticks with a heal above 0.075: L-0039 sight on 1089,
L-0040 sight on 1489 (728 ticks), L-0079 sight on 8608. Controls green today: heals happen in every one of
those fights, and L-0050 (no Wardens) has none of either.
"""
import pytest

import engine_rules_oracle as oracle

FIGHTS = [("L-0039", "on"), ("L-0040", "on"), ("L-0079", "on")]


@pytest.mark.parametrize("name,sight", FIGHTS)
def test_R_083_03_no_unit_heals_more_than_one_wardens_0_075_in_a_tick(name, sight):
    """R-083-03 / R-084-01, per tick over the whole fight with Wardens in the formation. Red today: 1089 / 1489 / 8608 unit-ticks of 0.150 or
    0.225 hp."""
    rec = oracle.played(name, sight)
    bad = oracle.warden_overheal(rec)
    assert not bad, "%s sight %s: %d unit-ticks healed more than %.3f (%d units), first %s" % (name, sight, len(bad), oracle.HEAL_ONE, oracle.distinct_units(bad), bad[:3])


@pytest.mark.parametrize("name,sight", FIGHTS)
def test_R_083_03_control_units_are_healed_in_these_fights(name, sight):
    """Control (green today and after): the fight contains more than 100 unit-ticks on which a unit unhit that tick gained hp, so a zero
    overheal count is the no-stacking rule at work, not a fight without healing."""
    rec = oracle.played(name, sight)
    gains = sum(1 for tk in rec.ticks for u in rec.ids if tk["pre"][u]["alive"] and tk["post"][u]["alive"]
                and tk["post"][u]["hp"] > tk["pre"][u]["hp"] + 1e-9 and u not in {b for _, b in tk["fires"]})
    assert gains > 100, "only %d unit-ticks with a heal" % gains


def test_R_083_03_control_a_fight_without_wardens_has_no_heal():
    """Control (green today): L-0050 has no Wardens; nothing heals and the oracle finds nothing."""
    rec = oracle.played("L-0050", "on")
    assert not oracle.warden_overheal(rec)
    assert not any(tk["post"][u]["hp"] > tk["pre"][u]["hp"] + 1e-9 for tk in rec.ticks for u in rec.ids if tk["pre"][u]["alive"] and tk["post"][u]["alive"])
