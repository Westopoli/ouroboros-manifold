# Rule pins: R-087-04, R-096-02, R-084-04, ALG-60
"""Engine rule fixes 2026-11-08, F2, whole fights: a unit that moves under its own power does not fire that tick; the 0.5 s pause after a
shot holds for every unit, group members included.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F2" and "Test architecture". Evidence: docs/reports/2026-11-07-rule-enforcement.md
(sweep I2a, I2as, I2b). Oracle: engine_rules_oracle.py in this directory (per tick, from engine state; not the F0 checker). The single-unit
and group scenes are tests/csim/test_E11_R087_04_a_moving_unit_does_not_fire.py.

Rule words: R-087-04 'walks toward it until the enemy is within attack range, then halts and fires'; R-096-02 an attack-moving unit halts
to fire and resumes; R-084-04 the 0.5 s pause after a shot (no own-power displacement in ticks 1 to 9 after it).
"Moved under its own power": displacement above 0.5 wu on the tick with no other unit within 40 wu (DRAFT-inv-push-radius, Westley's).

Measured on the unfixed tree (2026-11-08, seed 1, 100 simulated seconds), unit-ticks that fired while moving / moved inside the pause:
  L-0039 sight on 3 / 12     L-0050 sight off 20 / 0     L-0044 sight off 35 / 8     L-0079 sight on 12 / 10     L-0083 sight on 20 / 1
Controls green today: L-0050 sight on 0 / 0, and every fight fires many shots (the fix must not mute the units).
"""
import pytest

import engine_rules_oracle as oracle

FIGHTS = [("L-0039", "on"), ("L-0050", "off"), ("L-0044", "off"), ("L-0079", "on"), ("L-0083", "on")]


@pytest.mark.parametrize("name,sight", FIGHTS)
def test_R_087_04_no_unit_fires_on_a_tick_on_which_it_moved(name, sight):
    """R-087-04, per tick over the whole fight, on the real lab engine with walkers, boxes and (where the layout has it) sight: a shot is
    never fired on a tick on which the shooter moved under its own power. Red today: 3 / 20 / 35 / 12 / 20 unit-ticks."""
    rec = oracle.played(name, sight)
    bad = oracle.fired_while_moving(rec)
    assert not bad, "%s sight %s: %d shots fired by a moving unit (%d units), first %s" % (name, sight, len(bad), oracle.distinct_units(bad), bad[:3])


@pytest.mark.parametrize("name,sight", [("L-0039", "on"), ("L-0044", "off"), ("L-0079", "on")])
def test_R_084_04_no_unit_moves_in_the_pause_after_its_shot(name, sight):
    """R-084-04, per tick over the whole fight: ticks 1 to 9 after a shot are free of own-power displacement, for lone units and for
    attack-moved groups (the lab orders each side as one group). Red today: 12 / 8 / 10 unit-ticks (Bombards walking on a group's cap)."""
    rec = oracle.played(name, sight)
    bad = oracle.moved_in_backswing(rec)
    assert not bad, "%s sight %s: %d unit-ticks of movement inside the pause (%d units), first %s" % (name, sight, len(bad), oracle.distinct_units(bad), bad[:3])


@pytest.mark.parametrize("name,sight", FIGHTS + [("L-0050", "on")])
def test_R_087_04_control_the_units_still_fire(name, sight):
    """Control (green today and after): at least 100 shots in 100 simulated seconds, so a fix that skipped every shot would be caught here,
    and a zero above means the rule held, not that nobody shot."""
    rec = oracle.played(name, sight)
    assert sum(len(tk["fires"]) for tk in rec.ticks) >= 100


def test_R_087_04_control_an_open_field_with_sight_on_has_no_violation_today():
    """Control (green today): L-0050 with sight on has 0 / 0, so the oracle's moved-and-fired test is not a blanket 'true'."""
    rec = oracle.played("L-0050", "on")
    assert not oracle.fired_while_moving(rec) and not oracle.moved_in_backswing(rec)
